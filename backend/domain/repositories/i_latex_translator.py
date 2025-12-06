from abc import ABC, abstractmethod

from domain.entities.latex_file import LatexFile
from domain.entities.target_language import TargetLanguage


class ILatexTranslator(ABC):
    """
    A latex translator.
    """

    @abstractmethod
    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        """
        Translate a latex file to a target language.

        Args:
            latex_file (LatexFile): The latex file to translate.
            target_language (TargetLanguage): The target language to translate to.

        Returns:
            LatexFile: The translated latex file.
        """
        pass
