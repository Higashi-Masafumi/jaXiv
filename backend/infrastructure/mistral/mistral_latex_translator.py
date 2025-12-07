import asyncio
import re
from logging import getLogger

from mistralai import Mistral
from mistralai.models.assistantmessage import AssistantMessage
from mistralai.models.systemmessage import SystemMessage
from mistralai.models.toolmessage import ToolMessage
from mistralai.models.usermessage import UserMessage
from mistralai.types import UNSET, UNSET_SENTINEL

from domain.entities import LatexFile, TargetLanguage
from domain.repositories import ILatexTranslator
from utils.preprocess import optimize_latex_content


class MistralLatexTranslator(ILatexTranslator):
    def __init__(self, api_key: str):
        self._client = Mistral(api_key=api_key)
        self._logger = getLogger(__name__)

    async def translate(
        self,
        latex_file: LatexFile,
        target_language: TargetLanguage,
        max_workers: int = 10,
    ) -> LatexFile:
        self._logger.info(
            "Begin translating %s: content length %d",
            latex_file.path,
            len(latex_file.content),
        )
        latex_file.content = optimize_latex_content(latex_file.content)
        sections = self._split_section(latex_file.content)
        self._logger.info("Splitted into %d sections", len(sections))
        semaphore = asyncio.Semaphore(max_workers)

        async def translate_section(section: str) -> str:
            if len(section) == 0:
                self._logger.info("Skipping empty section")
                return ""
            async with semaphore:
                self._logger.info("Translating section length %d", len(section))
                messages: list[
                    AssistantMessage | SystemMessage | ToolMessage | UserMessage
                ] = [
                    SystemMessage(content=self._system_prompt(target_language)),
                    UserMessage(content=self._user_prompt(section)),
                ]
                chat_response = await self._client.chat.complete_async(
                    model="codestral-2501",
                    messages=messages,
                    stream=False,
                )
                message_content = chat_response.choices[0].message.content
                if message_content is None or message_content in (
                    UNSET,
                    UNSET_SENTINEL,
                ):
                    raise ValueError("Translated text is empty")
                if isinstance(message_content, list):
                    translated_text = "".join(str(x) for x in message_content)
                else:
                    translated_text = str(message_content)
                if translated_text == "":
                    raise ValueError("Translated text is empty")
                return self._extract_latex_content(translated_text)

        translated_latex_contents = await asyncio.gather(
            *[translate_section(section) for section in sections]
        )
        return LatexFile(
            path=latex_file.path,
            content="\n".join(translated_latex_contents),
        )

    @staticmethod
    def _system_prompt(target_language: TargetLanguage) -> str:
        return (
            f"あなたは、{target_language}のLatexの文法を熟知しているLatexの翻訳家です。"
            "与えられたLatexのソースコードを、Latexの文法を崩すことなく、翻訳してください。"
            "# 注意するべきLatexの文法\n"
            "1. コマンドはそのままにしてください。(`\\section`, `\\cite`, `\\begin{}`, `\\ `, math expressions like `$...$`, environments, labels, \\begin{document}, \\end{document}, etc.)\n"
            "2. `%`はlatexにおけるコメントアウトになるので文字として`%`を含めたい場合は`\\%`としてください。\n"
            "3. 数式中の記号 `\\(` `\\)` `$` `&` `\\` `{` `}` は **絶対に削除・全角化しない**。\n"
            "4. `\\label{}` `\\ref{}` `\\cite{}` で括られたキー名は **一文字も変更しない**。\n"
            "5. カスタムコマンドなど、一般的でないコマンドに関連するものは翻訳せず、そのままにしてください。明かに一般的なコマンドで囲まれている文章のみを翻訳してください。\n"
            "6. \\includegraphics は翻訳せず、画像パスをそのままにしてください\n"
            "# 注意事項\n"
            "単なるコマンドの定義ファイルの場合もあるので、その場合はそのままにしてください。\n"
            "# 出力形式\n"
            "```latex\n"
            "{translated_text}\n"
            "```"
        )

    @staticmethod
    def _user_prompt(section: str) -> str:
        return f"# 翻訳対象のlatexコード\n{section}\n"

    @staticmethod
    def _extract_latex_content(translated_text: str) -> str:
        """
        翻訳されたテキストからlatexのコード部分を抽出する
        ```latex
        {translated_text}
        ```
        や
        <latex>
        {translated_text}
        </latex>
        のような形式で出力されるので、それを抽出する
        """
        # ```latex ... ``` の抽出（複数行対応）
        pattern = r"```latex\s*\n(.*?)\n?```"
        match = re.search(pattern, translated_text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # <latex> ... </latex> の抽出（複数行対応）
        pattern = r"<latex>\s*\n?(.*?)\n?</latex>"
        match = re.search(pattern, translated_text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return translated_text.strip()

    @staticmethod
    def _split_section(latex_text: str) -> list[str]:
        """
        LaTeX文書を\\section または \\subsection で分割。
        どちらも存在しなければ全文を1要素で返す。
        """
        # ^\section{...}, ^\section*{...}, ^\subsection{...}, ^\subsection*{...} にマッチ
        pattern = re.compile(r"^\\(?:sub)?section\*?\{.*\}$", re.MULTILINE)
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
