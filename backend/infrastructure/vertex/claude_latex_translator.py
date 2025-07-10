import re
from domain.repositories import ILatexTranslator
from domain.entities import LatexFile, TargetLanguage
from anthropic import AnthropicVertex
from utils.preprocess import optimize_latex_content  # noqa: F401
from logging import getLogger


class ClaudeLatexTranslator(ILatexTranslator):
    def __init__(
        self,
        project_id: str,
        location: str,
        model_name: str,
    ):
        self._project_id = project_id
        self._location = location
        self._model_name = model_name
        self._client = AnthropicVertex(project_id=project_id, region=location)
        self._logger = getLogger(__name__)

    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        sections = self._split_section(latex_file.content)
        system_prompt = (
            f"あなたは、{target_language}のLatexの文法を熟知しているLatexの翻訳家です。与えられたLaTeXのソースコードのテキスト部分を、指定された言語に翻訳してください。"
            f"# 依頼事項\n"
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
        for i, section in enumerate(sections):
            section = optimize_latex_content(section)
            if section == "":
                self._logger.warning("Section %d is empty. Skip.", i)
                translated_sections.append(section)
                continue
            user_prompt = (
                f"[# 翻訳先言語]\n{target_language}\n"
                f"[# 翻訳対象のlatexコード]\n"
                f"{section}\n"
            )
            response = self._client.messages.create(
                model=self._model_name,
                system=system_prompt,
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )
            if response.content and len(response.content) > 0:
                from anthropic.types import TextBlock

                content_block = response.content[0]
                if isinstance(content_block, TextBlock):
                    translated_section = content_block.text
                else:
                    self._logger.error(
                        "Unexpected content type in response for section %d", i
                    )
                    translated_section = ""
            else:
                self._logger.error("Empty response content for section %d", i)
                translated_section = ""

            if not translated_section:
                self._logger.error("Failed to translate section %d", i)
                continue
            translated_section = self._clean_latex_text(translated_section)
            translated_sections.append(translated_section)

        return LatexFile(
            path=latex_file.path,
            content="\n".join(translated_sections),
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
