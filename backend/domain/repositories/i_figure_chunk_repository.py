from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, ConfigDict

from domain.entities.document_chunk import DocumentFigureChunk
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.pdf_paper_id import PdfPaperId

# Vector(s) to score figures against. ``image``/``caption`` use a single named
# vector; ``hybrid`` fuses both (reciprocal rank fusion). The query is always a
# nomic-embed-text vector, which is directly comparable to the nomic-embed-vision
# image vectors because the two models share one latent space.
FigureSearchMode = Literal['image', 'caption', 'hybrid']


class GlobalFigureHit(BaseModel):
	"""Lightweight result of a cross-paper figure similarity search.

	Unlike ``DocumentFigureChunk`` this does not carry the figure embeddings,
	since global suggestion only needs payload metadata plus the similarity
	score for ranking and deduplication.
	"""

	model_config = ConfigDict(frozen=True)

	paper_id: str
	image_url: str
	caption: str | None
	page_number: int
	score: float


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
		mode: FigureSearchMode = 'hybrid',
		limit: int = 5,
	) -> list[DocumentFigureChunk]:
		"""Query figure chunks by paper ID using vector similarity search."""
		...

	@abstractmethod
	async def query_global(
		self,
		query_embeddings: Embedding,
		mode: FigureSearchMode = 'hybrid',
		limit: int = 20,
	) -> list[GlobalFigureHit]:
		"""Query figure chunks across all papers using vector similarity search."""
		...
