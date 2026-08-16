from abc import ABC, abstractmethod
from pathlib import Path


class IFigureStorageRepository(ABC):
	"""Repository for uploading and managing figure files in external storage."""

	@abstractmethod
	async def upload_figures(self, paper_id: str, source_dir: Path) -> dict[str, str]:
		"""Upload all figure files from source_dir to storage.

		Args:
		    paper_id: Identifier used as a path prefix.
		    source_dir: Path to the directory containing figure files.

		Returns:
		    A dict mapping each figure's filename to its public URL.
		"""
		...

	@abstractmethod
	async def upload_figure_file(
		self,
		paper_id: str,
		filename: str,
		image_path: Path,
		content_type: str = 'image/png',
	) -> str:
		"""Upload an image file to storage and return the public URL.

		Takes a path rather than bytes so the image is streamed from disk instead
		of being held in memory for the duration of the upload.
		"""
		...

	@abstractmethod
	async def upload_pdf(self, paper_id: str, pdf_path: Path) -> str:
		"""Upload a PDF file to storage and return the public URL.

		Args:
		    paper_id: Identifier used as a path prefix.
		    pdf_path: Path to the PDF file to upload.

		Returns:
		    The public URL of the uploaded PDF.
		"""
		...
