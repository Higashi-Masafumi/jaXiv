from abc import ABC, abstractmethod

from domain.entities.latex_file import TranslatedLatexFile


class IFileStorageRepository(ABC):
	"""
	A repository for storing and retrieving files.
	"""

	@abstractmethod
	async def save_translated_latex_file_and_get_url(
		self, translated_latex_file: TranslatedLatexFile
	) -> str:
		"""
		Save a translated latex file and get the URL of the file.

		Args:
		    translated_latex_file (TranslatedLatexFile): The translated latex file to save.

		Returns:
		    str: The URL of the saved file.

		>>> translated_latex_file = TranslatedLatexFile(
		...     path='path/to/translated_latex_file.tex',
		...     storage_path='path/to/translated_latex_file.tex',
		... )
		>>> url = await save_translated_latex_file_and_get_url(translated_latex_file)
		>>> print(url)
		"https://example.com/translated_latex_file.tex"
		"""
		pass
