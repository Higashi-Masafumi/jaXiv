from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.figure import FigureWithEmbedding


class IPdfFigureAnalyzer(ABC):
	"""Gateway for extracting and embedding figures from PDF files."""

	@abstractmethod
	def analyze_figures(self, pdf_path: Path) -> list[FigureWithEmbedding]:
		"""Extract and embed figures from a PDF file."""
		...
