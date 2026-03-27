from abc import ABC, abstractmethod

from domain.entities.latex_file import TranslatedLatexFile


class IFileStorageRepository(ABC):
	"""Repository for storing and retrieving translated files."""

	@abstractmethod
	async def save_translated_file_and_get_url(
		self, translated_file: TranslatedLatexFile
	) -> str:
		"""
		Save a translated file and return its public URL.

		Args:
		    translated_file: The translated file to save.

		Returns:
		    The public URL of the saved file.
		"""
		...
