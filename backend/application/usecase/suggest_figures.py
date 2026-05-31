import asyncio

from pydantic import BaseModel, ConfigDict

from domain.gateways.i_figure_query_generator import IFigureQueryGenerator
from domain.gateways.i_query_embedding_gateway import IQueryEmbeddingGateway
from domain.repositories.i_blog_post_repository import IBlogPostRepository
from domain.repositories.i_figure_chunk_repository import GlobalFigureHit, IFigureChunkRepository


class FigureSuggestionItem(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_url: str
	caption: str | None
	page_number: int
	paper_id: str
	paper_title: str | None
	score: float
	matched_query: str


class SuggestFiguresResult(BaseModel):
	model_config = ConfigDict(frozen=True)

	queries: list[str]
	items: list[FigureSuggestionItem]


class SuggestFiguresUseCase:
	"""Suggest reference figures across all papers from a free-form description.

	The user's input is expanded into several diverse search queries (via the
	figure query generator). Each query is embedded and run as a global vector
	search over the figure collection. Hits are merged/deduped by image URL
	(keeping the best score) and enriched with their source paper titles.
	"""

	def __init__(
		self,
		query_generator: IFigureQueryGenerator,
		query_embedding: IQueryEmbeddingGateway,
		figure_chunk_repository: IFigureChunkRepository,
		blog_post_repository: IBlogPostRepository,
	):
		self._query_generator = query_generator
		self._query_embedding = query_embedding
		self._figure_chunk_repository = figure_chunk_repository
		self._blog_post_repository = blog_post_repository

	async def execute(
		self,
		user_input: str,
		limit: int = 24,
		n_queries: int = 4,
	) -> SuggestFiguresResult:
		queries = await self._query_generator.generate_queries(user_input, n_queries)
		if not queries:
			queries = [user_input]

		async def search_one(query: str) -> list[tuple[GlobalFigureHit, str]]:
			emb = await self._query_embedding.embed_query(query, 'nomic')
			hits = await self._figure_chunk_repository.query_global(
				emb,
				using='caption',
				limit=limit,
			)
			return [(hit, query) for hit in hits]

		results = await asyncio.gather(*[search_one(q) for q in queries])

		# Merge/dedupe by image_url, keeping the hit with the highest score.
		best: dict[str, tuple[GlobalFigureHit, str]] = {}
		for hits in results:
			for hit, query in hits:
				existing = best.get(hit.image_url)
				if existing is None or hit.score > existing[0].score:
					best[hit.image_url] = (hit, query)

		ranked = sorted(best.values(), key=lambda pair: pair[0].score, reverse=True)[:limit]

		titles = await self._blog_post_repository.find_titles_by_paper_ids(
			list({hit.paper_id for hit, _ in ranked})
		)

		return SuggestFiguresResult(
			queries=queries,
			items=[
				FigureSuggestionItem(
					image_url=hit.image_url,
					caption=hit.caption,
					page_number=hit.page_number,
					paper_id=hit.paper_id,
					paper_title=titles.get(hit.paper_id) or None,
					score=hit.score,
					matched_query=query,
				)
				for hit, query in ranked
			],
		)
