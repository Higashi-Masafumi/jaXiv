from abc import ABC, abstractmethod

from domain.entities.document_chunk import DocumentTextChunk
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.pdf_paper_id import PdfPaperId


class ITextChunkRepository(ABC):
	"""Repository for persisting and retrieving text chunks."""

	@abstractmethod
	async def save(self, chunk: DocumentTextChunk) -> None:
		"""Save a text chunk."""
		...

	@abstractmethod
	async def query(
		self,
		paper_id: ArxivPaperId | PdfPaperId,
		query_embeddings: Embedding,
		limit: int = 5,
	) -> list[DocumentTextChunk]:
		"""Query text chunks by paper ID using vector similarity search."""
		...
