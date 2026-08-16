from abc import ABC, abstractmethod
from pathlib import Path


class IFileStorageRepository(ABC):
	"""Repository for storing translated PDFs."""

	@abstractmethod
	async def save_translated_file_and_get_url(
		self,
		storage_path: str,
		file_path: Path,
	) -> str:
		"""Upload the file at ``file_path`` to ``storage_path`` and return its public URL.

		Takes a path rather than bytes so a translated PDF is streamed from disk
		instead of being held in memory for the duration of the upload.
		"""
