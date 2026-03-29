from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.extracted_figure import ExtractedFigure


class IPdfFigureExtractor(ABC):
	"""Gateway for extracting figures from PDF files."""

	@abstractmethod
	def extract_figures(self, pdf_path: Path) -> list[ExtractedFigure]:
		"""Extract figures with captions from a PDF file."""
		...
