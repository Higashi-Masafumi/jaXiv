from domain.repositories import ILatexTranslator
from domain.entities.latex_file import LatexFile
from domain.entities.target_language import TargetLanguage
from utils.preprocess import (
    optimize_latex_content,
    replace_escaped_latex_commands_with_html_entities,
)
from utils.postprocess import replace_html_entities_with_latex_commands
from logging import getLogger
from google.cloud import translate_v3
import re
import asyncio


class CloudLatexTranslator(ILatexTranslator):
    def __init__(self, project_id: str):
        self._logger = getLogger(__name__)
        self._project_id = project_id

    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        sections = self._split_section(latex_file.content)
        self._logger.info(f"Translating {len(sections)} sections")
        client = translate_v3.TranslationServiceAsyncClient()
        tasks = [
            self._translate_section(client, section, target_language)
            for section in sections
        ]
        results = await asyncio.gather(*tasks)
        return LatexFile(content="\n\n".join(results), path=latex_file.path)

    async def _translate_section(
        self,
        client: translate_v3.TranslationServiceAsyncClient,
        section: str,
        target_language: TargetLanguage,
    ) -> str:
        if target_language == TargetLanguage.JAPANESE:
            target_language_code = "ja"

        section = optimize_latex_content(section)
        section = replace_escaped_latex_commands_with_html_entities(section)
        self._logger.info(f"Optimized section: {len(section)}")

        response = await client.translate_text(
            parent=f"projects/{self._project_id}",
            contents=[section],
            target_language_code=target_language_code,
            mime_type="text/plain",
        )
        translated = response.translations[0].translated_text
        translated = replace_html_entities_with_latex_commands(translated)
        return translated

    @staticmethod
    def _split_section(latex_text: str) -> list[str]:
        # 2つ以上の連続した改行で分割
        blocks = re.split(r"\n{2,}", latex_text)
        # 空要素や空白のみの要素を除外し、stripして返す
        return [block.strip() for block in blocks if block.strip()]
