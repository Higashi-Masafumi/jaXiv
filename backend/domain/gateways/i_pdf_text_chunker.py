from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.text_chunk import TextChunkWithEmbedding


class IPdfChunkAnalyzer(ABC):
	"""Gateway for chunking and embedding text from PDF files."""

	@abstractmethod
	def analyze_chunks(self, pdf_path: Path) -> list[TextChunkWithEmbedding]:
		"""Chunk and embed text from a PDF file."""
		...
