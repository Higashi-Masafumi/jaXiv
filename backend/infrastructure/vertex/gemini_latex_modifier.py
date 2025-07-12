from domain.repositories import ILatexModifier
from domain.entities.latex_file import LatexFile
from domain.entities.compile_error import CompileError
from google import genai
from google.genai import types
from logging import getLogger
import re
import time


class VertexGeminiLatexModifier(ILatexModifier):
    """
    A modifier for LaTeX files using Gemini.
    """

    def __init__(self, project_id: str, location: str):
        self._logger = getLogger(__name__)
        self._client = genai.Client(
            vertexai=True, project=project_id, location=location
        )

    async def modify(
        self, latex_file: LatexFile, compile_error: CompileError
    ) -> LatexFile:
        """
        LaTeXファイルのコンパイルエラーを修正する。
        """
        self._logger.info(
            "Modifying LaTeX file: %s, Error type: %s",
            latex_file.path,
            compile_error.error_type,
        )

        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(
            latex_file.content, compile_error.error_message
        )

        start_time = time.time()

        response = self._client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )

        if response.text is None:
            raise ValueError("Failed to modify LaTeX file")

        modified_content = self._clean_latex_text(response.text)

        self._logger.info(
            "Modified LaTeX file in %f seconds, %d tokens",
            time.time() - start_time,
            response.usage_metadata.total_token_count if response.usage_metadata else 0,
        )

        return LatexFile(path=latex_file.path, content=modified_content)

    def _create_system_prompt(self) -> str:
        """LaTeX修正用のシステムプロンプトを作成"""
        return (
            "あなたは、LaTeXの専門家です。Cloud Translation（Google翻訳）によって翻訳されたLaTeXコードの修正を行ってください。"
            "この修正対象ファイルは、LaTeXプロジェクト全体の一部ファイルであり、翻訳過程で構文エラーが発生している可能性があります。"
            "\n\n# 翻訳過程で発生しやすいエラーパターン\n"
            "1. **構文の破損**:\n"
            "   - 波括弧 {} の対応ミス（翻訳時に削除・追加されてしまった）\n"
            "   - バックスラッシュ \\\\ の欠落（翻訳で削除されてしまった）\n"
            "   - 環境の不一致（\\begin{}と\\end{}のペアの破損）\n"
            "   - 数式記号の破損（$, \\(, \\), &, \\\\ などの削除・全角化）\n"
            "\n"
            "2. **翻訳すべきでない部分の翻訳**:\n"
            "   - LaTeXコマンド名の翻訳（例: \\section → \\セクション）\n"
            "   - カスタム環境名の翻訳（例: \\begin{theorem} → \\begin{定理}）\n"
            "   - ラベル名・参照名の翻訳（例: \\label{intro} → \\label{はじめに}）\n"
            "   - パッケージ名の翻訳\n"
            "\n"
            "# 修正方針\n"
            "- **絶対に新しい\\usepackage{}や\\newcommand{}を追加しないでください**\n"
            "- **最小限の修正のみ**行い、翻訳で破損した構文のみを修復してください\n"
            "- **文書の内容や構造は変更せず**、LaTeXの構文エラーのみを修正してください\n"
            "- **翻訳されたテキスト部分はそのまま**にして、LaTeX構文のみを修正してください\n"
            "- **{}の対応関係が成り立っているかどうかを確認して、不足している`}`を追加してください**\n"
            "- **元のLaTeXプロジェクト全体の文脈**を考慮し、部分ファイルとして正しく動作するように修正してください\n"
            "\n"
            "# 修正例\n"
            "間違った修正: 新しいパッケージやコマンドの追加\n"
            "正しい修正: \\section{はじめに → \\section{はじめに}\n"
            "正しい修正: \\caption{\textbf{\tool{}は、他の手法よりも忠実度の高い生のスコアとサリエンシーマップを生成し、ImageNet-Segmentationタスクによって提供される真のサリエンシーマップの品質さえも凌駕することがあります。上段は各手法のソフト予測を示し、下段は2値化予測を示しています。 } → \\caption{\textbf{\tool{}}は、他の手法よりも忠実度の高い生のスコアとサリエンシーマップを生成し、ImageNet-Segmentationタスクによって提供される真のサリエンシーマップの品質さえも凌駕することがあります。上段は各手法のソフト予測を示し、下段は2値化予測を示しています。 }\n"
            "正しい修正: \\begin{定理} → \\begin{theorem}\n"
            "正しい修正: $x^2$ の全角文字を半角に修正\n"
            "\n"
            "# 出力形式\n"
            "修正後のLaTeXコードのみを出力してください。説明文やコードブロック記号は一切使用しないでください。"
        )

    def _create_user_prompt(self, latex_content: str, error_message: str) -> str:
        """ユーザープロンプトを作成"""
        return (
            f"以下は、Cloud Translation（Google翻訳）によって翻訳された後のLaTeXコードです。\n"
            f"翻訳過程でLaTeX構文が破損し、コンパイルエラーが発生しています。\n"
            f"このファイルはLaTeXプロジェクト全体の一部であることを考慮して、最小限の修正を行ってください。\n\n"
            f"[# 発生したコンパイルエラー]\n"
            f"{error_message}\n\n"
            f"[# 翻訳後のLaTeXコード（修正対象）]\n"
            f"{latex_content}\n"
        )

    @staticmethod
    def _clean_latex_text(latex_text: str) -> str:
        """
        Geminiの出力から不要なコードブロックやタグを除去する。
        """
        # ```latex ... ``` を除去
        latex_text = re.sub(r"```latex\s*([\s\S]*?)```", r"\1", latex_text)
        # ``` ... ``` を除去
        latex_text = re.sub(r"```\s*([\s\S]*?)```", r"\1", latex_text)
        # <latex> ... </latex> を除去
        latex_text = re.sub(r"<latex>\s*([\s\S]*?)\s*</latex>", r"\1", latex_text)
        # 単独の```を除去
        latex_text = re.sub(r"```", "", latex_text)
        return latex_text.strip()
