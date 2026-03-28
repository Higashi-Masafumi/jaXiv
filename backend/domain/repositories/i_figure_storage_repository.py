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
	async def upload_figure_bytes(
		self,
		paper_id: str,
		filename: str,
		data: bytes,
		content_type: str = 'image/png',
	) -> str:
		"""Upload raw image bytes to storage and return the public URL."""
		...
