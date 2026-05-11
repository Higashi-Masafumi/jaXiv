from abc import ABC, abstractmethod


class IFileStorageRepository(ABC):
	"""Repository for storing translated PDFs."""

	@abstractmethod
	async def save_translated_file_and_get_url(
		self,
		storage_path: str,
		content: bytes,
	) -> str:
		"""Upload ``content`` to ``storage_path`` and return its public URL."""
