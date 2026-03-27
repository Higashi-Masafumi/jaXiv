from abc import ABC, abstractmethod

from domain.entities.latex_file import LatexFile
from domain.value_objects import TargetLanguage


class ILatexTranslator(ABC):
	"""Gateway for translating LaTeX files using an LLM."""

	@abstractmethod
	async def translate(self, latex_file: LatexFile, target_language: TargetLanguage) -> LatexFile:
		"""
		Translate a LaTeX file to the target language.

		Args:
		    latex_file: The LaTeX file to translate.
		    target_language: The target language.

		Returns:
		    The translated LaTeX file.

		Raises:
		    TranslationFailedError: If translation fails.
		    TranslationEmptyResultError: If the result is empty.
		"""
		...
