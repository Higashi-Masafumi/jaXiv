from abc import ABC, abstractmethod

from domain.entities.document_chunk import DocumentChunk, DocumentFigureChunk, DocumentTextChunk
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.pdf_paper_id import PdfPaperId


class IDocumentChunkRepository(ABC):
	"""Repository for persisting and retrieving document chunks."""

	@abstractmethod
	async def save_text_chunk(self, text_chunk: DocumentTextChunk) -> None:
		"""Save a text chunk."""
		...

	@abstractmethod
	async def save_figure_chunk(self, figure_chunk: DocumentFigureChunk) -> None:
		"""Save a figure chunk."""
		...

	@abstractmethod
	async def query_chunks(
		self, paper_id: ArxivPaperId | PdfPaperId, query_embeddings: Embedding
	) -> list[DocumentChunk]:
		"""Query chunks by paper ID."""
		...
