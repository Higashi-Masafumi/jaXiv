from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.pdf_paper import PdfPaperMetadata


class IPdfMetadataExtractor(ABC):
	"""Gateway for extracting metadata (title, authors, abstract) from PDF files."""

	@abstractmethod
	def extract_metadata(self, pdf_path: Path) -> PdfPaperMetadata:
		"""Extract metadata from a PDF file."""
		...
