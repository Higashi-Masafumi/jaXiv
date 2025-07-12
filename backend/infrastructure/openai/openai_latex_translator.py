from domain.repositories import ILatexTranslator
from domain.entities.latex_file import LatexFile
from domain.entities.target_language import TargetLanguage
from logging import getLogger
from openai import OpenAI
import asyncio
import time
import re
from utils import optimize_latex_content


class OpenaiLatexTranslator(ILatexTranslator):
    def __init__(self, api_key: str):
        self._logger = getLogger(__name__)
        self._client = OpenAI(api_key=api_key)

    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        sections = self._split_section(latex_file.content)
        translated_sections: list[str] = []
        self._logger.info("Begin translating %d sections", len(sections))
        # 並列実行数を制限する
        semaphore = asyncio.Semaphore(5)

        async def translate_section(
            section: str, target_language: TargetLanguage
        ) -> str:
            async with semaphore:
                return await self._translate_section(section, target_language)

        translation_tasks = [
            translate_section(section, target_language) for section in sections
        ]
        translated_sections = await asyncio.gather(*translation_tasks)
        return LatexFile(path=latex_file.path, content="\n".join(translated_sections))

    async def _translate_section(
        self,
        section: str,
        target_language: TargetLanguage,
    ) -> str:
        system_prompt = (
            f"あなたは、{target_language}のLatexの文法を熟知しているLatexの翻訳家です。与えられたLaTeXのソースコードのテキスト部分を、指定された言語に翻訳してください。"
            "あくまで翻訳するのはテキスト部分のみであり、latexのコードはそのままにしてください。"
            "自然な翻訳となるように注意してください。"
            "# 依頼事項\n"
            "1. コマンドはそのままにしてください。(`\\section`, `\\cite`, `\\begin{}`, `\\ `, math expressions like `$...$`, environments, labels, \\begin{document}, \\end{document}, etc.)\n"
            "2. 自然言語の部分のみを翻訳してください。(section titles, paragraph text, abstract, captions, keywords, etc.)\n"
            "3. コード、数式、参照、ファイルパス、句読点、フォーマットはそのままにしてください。また、空白を勝手に削除しないでください。\n"
            "4. 与えられるLatexのソースコードは一部のみであるので、\\begin{document}と\\end{document}を補完したり、削除したりしてはいけません。\n"
            "5. カスタムコマンドなど、一般的でないコマンドに関連するものは翻訳せず、そのままにしてください。\n"
            "6. 数式中の記号 `\\(` `\\)` `$` `&` `\\` `{` `}` は **絶対に削除・全角化しない**。\n"
            "7. `\\label{}` `\\ref{}` `\\cite{}` で括られたキー名は **一文字も変更しない**。\n"
            "8. `%`はlatexにおけるコメントアウトになるので文字として`%`を含めたい場合は`\\%`としてください。\n"
            "# 例\n"
            "<入力>\n"
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\section{Introduction}\n"
            "This paper studies turbulence in galaxy clusters $\\approx100\\%$,km,s$^{-1}$. \\ This is a test."
            "<出力>\n"
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\section{はじめに}\n"
            "本論文では銀河団の乱流（$\\approx100\\%$,km,s$^{-1}$）を研究します。\\ これはテストです。"
            "# 注意事項\n"
            "[# 翻訳対象のlatexコード]で翻訳対象のlatexコードを与えます。\n"
            "[# 翻訳先言語]で翻訳先の言語を指定します。\n"
        )
        start_time = time.time()
        # latexコードから不要なコードブロックを除去
        section = optimize_latex_content(section)
        if section == "":
            self._logger.warning(
                "\t---\n\tEmpty section: %s, Skip\n\t---",
                section,
            )
            return ""
        user_prompt = (
            f"[# 翻訳先言語]\n{target_language}\n"
            f"[# 翻訳対象のlatexコード]\n"
            f"{section}\n"
        )
        response = self._client.responses.create(
            model="gpt-4o",
            input=user_prompt,
            instructions=system_prompt,
        )
        translated_section = response.output_text
        if translated_section is None:
            raise ValueError("Failed to translate section")
        self._logger.info(
            "Translated section in %f seconds, %d tokens",
            time.time() - start_time,
            response.usage.total_tokens if response.usage else 0,
        )
        translated_section = self._clean_latex_text(translated_section)
        return translated_section

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

    @staticmethod
    def _clean_latex_text(latex_text: str) -> str:
        """
        Geminiの出力から不要なコードブロックやタグを除去する。
        """
        # ```latex ... ``` を除去
        latex_text = re.sub(r"```latex\s*([\s\S]*?)```", r"\1", latex_text)
        # <latex> ... </latex> を除去
        latex_text = re.sub(r"<latex>\s*([\s\S]*?)\s*</latex>", r"\1", latex_text)
        # 他の可能性として ```だけ のものも除去
        latex_text = re.sub(r"```", "", latex_text)
        return latex_text.strip()
