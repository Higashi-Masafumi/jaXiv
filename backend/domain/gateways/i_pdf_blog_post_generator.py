from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.extracted_figure import UploadedFigure
from domain.entities.pdf_paper import PdfPaperMetadata


class IPdfBlogPostGenerator(ABC):
	"""Interface for generating blog posts from PDF papers."""

	@abstractmethod
	async def generate_from_pdf(
		self,
		paper_metadata: PdfPaperMetadata,
		pdf_path: Path,
		figures: list[UploadedFigure],
	) -> str: ...
