from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.figure import ExtractedFigure


class IPdfFigureExtractor(ABC):
	"""Gateway for extracting figures from PDF files."""

	@abstractmethod
	async def extract_figures(self, pdf_path: Path, image_dir: Path) -> list[ExtractedFigure]:
		"""Extract figures with captions from a PDF file.

		Args:
		    pdf_path: PDF to extract from.
		    image_dir: Directory the extracted images are written to. The caller
		        owns it and is responsible for deleting it once the figures have
		        been consumed.
		"""
		...
