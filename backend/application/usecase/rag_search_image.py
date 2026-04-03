from pydantic import BaseModel, ConfigDict

from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.pdf_paper_id import PdfPaperId
from domain.gateways.i_query_embedding_gateway import IQueryEmbeddingGateway
from domain.repositories.i_figure_chunk_repository import IFigureChunkRepository


class RagImageHit(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_url: str
	caption: str | None
	page_number: int


class RagSearchImageResult(BaseModel):
	model_config = ConfigDict(frozen=True)

	items: list[RagImageHit]


class RagSearchImageUseCase:
	def __init__(
		self,
		query_embedding: IQueryEmbeddingGateway,
		figure_chunk_repository: IFigureChunkRepository,
	):
		self._query_embedding = query_embedding
		self._figure_chunk_repository = figure_chunk_repository

	async def execute(
		self,
		paper_id: ArxivPaperId | PdfPaperId,
		query: str,
		limit: int = 5,
	) -> RagSearchImageResult:
		emb = await self._query_embedding.embed_query(query, 'nomic')
		chunks = await self._figure_chunk_repository.query(
			paper_id,
			emb,
			using='caption',
			limit=limit,
		)
		return RagSearchImageResult(
			items=[
				RagImageHit(
					image_url=str(c.image_url.root),
					caption=c.caption,
					page_number=c.page_number,
				)
				for c in chunks
			]
		)
