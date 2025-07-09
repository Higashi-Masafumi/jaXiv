from domain.entities.target_language import TargetLanguage
from domain.repositories import ILatexTranslator
from domain.entities.latex_file import LatexFile
from logging import getLogger
from google import genai
from google.genai import types
from utils import optimize_latex_content
import re
import time


class GeminiLatexTranslator(ILatexTranslator):
    """
    A translator for LaTeX files using Gemini.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._logger = getLogger(__name__)
        self._client = genai.Client(api_key=api_key)

    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        sections = self._split_section(latex_file.content)
        system_prompt = (
            "あなたは、Latexの文法を熟知しているLatexの翻訳家です。与えられたLaTeXのソースコードのテキスト部分を、指定された言語に翻訳してください。\n"
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
            "本論文では銀河団の乱流（$\approx100\\%$,km,s$^{-1}$）を研究します。\\ これはテストです。"
            "# 注意事項\n"
            "[# 翻訳対象のlatexコード]で翻訳対象のlatexコードを与えます。\n"
            "[# 翻訳先言語]で翻訳先の言語を指定します。\n"
        )
        translated_sections: list[str] = []
        self._logger.info("Begin translating %d sections", len(sections))
        for i, section in enumerate(sections):
            self._logger.info("Translating section %d", i)
            # 前処理
            section = optimize_latex_content(section)
            start_time = time.time()
            user_prompt = (
                f"[# 翻訳先言語]\n{target_language}\n"
                f"[# 翻訳対象のlatexコード]\n"
                f"{section}\n"
            )
            response = self._client.models.generate_content(
                model="gemini-2.5-pro",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
                contents=[user_prompt],
            )
            translated_section = response.text
            if translated_section is None:
                raise ValueError("Failed to translate section")
            translated_section = self._clean_latex_text(translated_section)
            num_tokens = (
                response.usage_metadata.prompt_token_count
                if response.usage_metadata
                else (
                    0 + response.usage_metadata.candidates_token_count
                    if response.usage_metadata
                    else 0
                )
            )
            if translated_section is None:
                raise ValueError("Failed to translate section")
            end_time = time.time()
            self._logger.info(
                "Translated section %d in %f seconds, %d tokens",
                i,
                end_time - start_time,
                num_tokens,
            )
            translated_sections.append(translated_section)
        return LatexFile(
            content="\n".join(translated_sections),
            path=latex_file.path,
        )

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
