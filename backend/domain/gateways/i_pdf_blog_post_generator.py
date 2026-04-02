from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.figure import UploadedPdfFigure
from domain.entities.pdf_paper import PdfPaperMetadata


class IPdfBlogPostGenerator(ABC):
	"""Interface for generating blog posts from PDF papers.

	``generate_from_pdf`` extracts paper metadata (title, authors, summary)
	and generates the blog post content in a single LLM call.
	"""

	@abstractmethod
	async def generate_from_pdf(
		self,
		pdf_path: Path,
		figures: list[UploadedPdfFigure],
	) -> tuple[PdfPaperMetadata, str]:
		"""Return ``(metadata, markdown_content)`` extracted from the PDF."""
		...
