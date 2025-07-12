from domain.entities.target_language import TargetLanguage
from domain.repositories import ILatexTranslator
from domain.entities.latex_file import LatexFile
from logging import getLogger
from google import genai
from google.genai import types
from utils.preprocess import optimize_latex_content
import re
import time


class VertexGeminiLatexTranslator(ILatexTranslator):
    """
    A translator for LaTeX files using Gemini.
    """

    def __init__(self, project_id: str, location: str):
        self._logger = getLogger(__name__)
        self._client = genai.Client(
            vertexai=True, project=project_id, location=location
        )

    async def translate(
        self, latex_file: LatexFile, target_language: TargetLanguage
    ) -> LatexFile:
        optimized_latex_content = optimize_latex_content(latex_file.content)
        system_prompt = (
            "あなたは、Latexを翻訳してください"
            "ただし、latexの文法は保ったままにしてください。"
            "# 注意するべきlatexの文法\n"
            "1. latexにおけるコメントアウトは`%`で行う、もし`%`を含めたい場合は`\\%`としてください。すなわち`\\%`は`\\%`と翻訳しないといけません"
            "2. 数式中の記号 `\\(` `\\)` `$` `&` `\\` `{` `}` は **絶対に削除・全角化しない**。"
            "3. `\\label{}` `\\ref{}` `\\cite{}` で括られたキー名は **一文字も変更しない**。"
            "4. `\\begin{document}`と`\\end{document}`は絶対に削除しないでください。"
            "5. カスタムコマンドなど、一般的でないコマンドに関連するものは翻訳せず、そのままにしてください。"
            "6. 数式中の記号 `\\(` `\\)` `$` `&` `\\` `{` `}` は **絶対に削除・全角化しない**。"
            "7. `\\label{}` `\\ref{}` `\\cite{}` で括られたキー名は **一文字も変更しない**。"
        )
        user_prompt = (
            f"次に与えるlatexを{target_language}に翻訳してください。"
            "ただし、latexの文法は保ったままにしてください。"
            "コマンドのみが定義されたファイルの場合もあるのでその時は翻訳せずにそのまま返してください。"
            "\n\n"
            f"[# 翻訳対象のlatexコード]\n"
            f"{optimized_latex_content}\n"
        )
        start_time = time.time()
        response = await self._client.aio.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=1.0,
            ),
            contents=[user_prompt],
        )
        translated_content = response.text
        self._logger.info(
            "Translated LaTeX file in %f seconds, %d tokens",
            time.time() - start_time,
            response.usage_metadata.total_token_count if response.usage_metadata else 0,
        )

        if translated_content is None:
            raise ValueError("Failed to translate latex")

        translated_content = self._clean_latex_text(translated_content)

        translated_latex_file = LatexFile(
            path=latex_file.path,
            content=translated_content,
        )
        return translated_latex_file

    def _clean_latex_text(self, latex_text: str) -> str:
        """
        Geminiの出力から不要なコードブロックやタグを除去する。
        ```latex ... ```の中身を抽出する
        それがなかったら
        <latex> ... </latex>の中身を抽出する
        それがなかったら
        ``` ... ```の中身を抽出する
        それがなかったら
        latex_textをそのまま返す
        """
        pattern = re.compile(r"```latex\s*([\s\S]*?)```", re.MULTILINE)
        match = pattern.search(latex_text)
        if match:
            return match.group(1)

        pattern = re.compile(r"<latex>\s*([\s\S]*?)</latex>", re.MULTILINE)
        match = pattern.search(latex_text)
        if match:
            return match.group(1)

        pattern = re.compile(r"```\s*([\s\S]*?)```", re.MULTILINE)
        match = pattern.search(latex_text)
        if match:
            return match.group(1)

        return latex_text