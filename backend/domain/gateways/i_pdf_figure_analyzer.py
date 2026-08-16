from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.figure import FigureWithEmbedding


class IPdfFigureAnalyzer(ABC):
	"""Gateway for extracting and embedding figures from PDF files."""

	@abstractmethod
	async def analyze_figures(self, pdf_path: Path, image_dir: Path) -> list[FigureWithEmbedding]:
		"""Extract and embed figures from a PDF file.

		Args:
		    pdf_path: PDF to analyze.
		    image_dir: Directory the extracted images are written to. The caller
		        owns it and is responsible for deleting it once the figures have
		        been uploaded.
		"""
		...

	@abstractmethod
	async def analyze_figures_from_url(
		self, pdf_url: str, image_dir: Path
	) -> list[FigureWithEmbedding]:
		"""Extract and embed figures from a PDF fetched by HTTPS URL.

		``image_dir`` follows the same ownership rule as ``analyze_figures``.
		"""
		...
