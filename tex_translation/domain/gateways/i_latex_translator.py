from abc import ABC, abstractmethod

from domain.entities import LatexFile
from domain.value_objects import TargetLanguage


class ILatexTranslator(ABC):
    """Gateway for translating LaTeX files using an LLM."""

    @abstractmethod
    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        """Translate ``latex_file`` to ``target_language``.

        Raises:
            TranslationFailedError: When the translator fails.
            TranslationEmptyResultError: When the result is empty.
        """
