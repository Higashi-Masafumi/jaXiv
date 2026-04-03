from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.text_chunk import TextChunkWithEmbedding


class IPdfChunkAnalyzer(ABC):
	"""Gateway for chunking and embedding text from PDF files."""

	@abstractmethod
	async def analyze_chunks(self, pdf_path: Path) -> list[TextChunkWithEmbedding]:
		"""Chunk and embed text from a PDF file."""
		...

	@abstractmethod
	async def analyze_chunks_from_url(self, pdf_url: str) -> list[TextChunkWithEmbedding]:
		"""Chunk and embed text from a PDF fetched by HTTPS URL (layout-analysis by-url API)."""
		...
