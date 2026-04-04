from abc import ABC, abstractmethod
from typing import Literal

from domain.entities.document_chunk import DocumentFigureChunk
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.pdf_paper_id import PdfPaperId


class IFigureChunkRepository(ABC):
	"""Repository for persisting and retrieving figure chunks."""

	@abstractmethod
	async def save(self, chunk: DocumentFigureChunk) -> None:
		"""Save a figure chunk."""
		...

	@abstractmethod
	async def query(
		self,
		paper_id: ArxivPaperId | PdfPaperId,
		query_embeddings: Embedding,
		using: Literal['image', 'caption'] = 'caption',
		limit: int = 5,
	) -> list[DocumentFigureChunk]:
		"""Query figure chunks by paper ID using vector similarity search."""
		...
