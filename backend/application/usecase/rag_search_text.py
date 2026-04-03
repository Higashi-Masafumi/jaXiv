from pydantic import BaseModel, ConfigDict

from domain.gateways.i_query_embedding_gateway import IQueryEmbeddingGateway
from domain.repositories.i_text_chunk_repository import ITextChunkRepository
from domain.value_objects.blog_paper_id import BlogPaperId


class RagTextHit(BaseModel):
	model_config = ConfigDict(frozen=True)

	text: str
	page_number: int


class RagSearchTextResult(BaseModel):
	model_config = ConfigDict(frozen=True)

	chunks: list[RagTextHit]


class RagSearchTextUseCase:
	def __init__(
		self,
		query_embedding: IQueryEmbeddingGateway,
		text_chunk_repository: ITextChunkRepository,
	):
		self._query_embedding = query_embedding
		self._text_chunk_repository = text_chunk_repository

	async def execute(
		self,
		paper_id: str,
		query: str,
		limit: int = 5,
	) -> RagSearchTextResult:
		blog_paper_id = BlogPaperId.from_raw(paper_id)
		emb = await self._query_embedding.embed_query(query, 'bge')
		chunks = await self._text_chunk_repository.query(
			blog_paper_id.root,
			emb,
			limit=limit,
		)
		return RagSearchTextResult(
			chunks=[RagTextHit(text=c.text, page_number=c.page_number) for c in chunks]
		)
