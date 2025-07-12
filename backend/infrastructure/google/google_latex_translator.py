from googletrans import Translator
from domain.repositories import ILatexTranslator
from domain.entities.latex_file import LatexFile
from domain.entities.target_language import TargetLanguage
from logging import getLogger
from typing_extensions import deprecated
import re
import asyncio


@deprecated(
    "This is unofficial API. Only for testing purpose. Use Cloud Translation instead."
)
class GoogleLatexTranslator(ILatexTranslator):
    def __init__(self):
        self._logger = getLogger(__name__)
        self._translator = Translator()

    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        sections = self._split_section(latex_file.content)
        self._logger.info(f"Translating {len(sections)} sections")
        tasks = []
        for i, section in enumerate(sections):
            self._logger.info(f"Translating section: {i+1} characters: {len(section)}")
            tasks.append(self._translate_section(section, target_language))
        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            sections[i] = result
        return LatexFile(content="\n".join(sections), path=latex_file.path)

    async def _translate_section(
        self, section: str, target_language: TargetLanguage
    ) -> str:
        section = section.replace("{", "<")
        section = section.replace("}", ">")
        translated_section = await self._translator.translate(
            section, dest=target_language.value
        )
        translated_section.text = translated_section.text.replace("<", "{")
        translated_section.text = translated_section.text.replace(">", "}")
        return translated_section.text

    @staticmethod
    def _split_section(latex_text: str) -> list[str]:
        """
        LaTeX文書を\\sectionで分割。
        \\sectionがなければ全文を1要素で返す。
        """
        pattern = re.compile(r"^\\section(\*?){.*}$", re.MULTILINE)
        matches = list(pattern.finditer(latex_text))

        if not matches:
            return [latex_text.strip()]

        blocks = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(latex_text)
            blocks.append(latex_text[start:end].strip())

        # \sectionの前にテキストがあれば先頭に追加
        pre_text = latex_text[: matches[0].start()].strip()
        if pre_text:
            blocks.insert(0, pre_text)

        return blocks
