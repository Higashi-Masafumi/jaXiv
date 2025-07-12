import asyncio
import time
from google import genai
from google.genai import types
from domain.entities import TargetLanguage
from utils.latex_translator_base import BaseLatexTranslator


class VertexGeminiLatexTranslator(BaseLatexTranslator):
    """Vertex AI Gemini を使用したLaTeX翻訳器"""

    def _init_specific(self, project_id: str, location: str):
        """Gemini固有の初期化"""
        self._project_id = project_id
        self._location = location
        self._client = genai.Client(
            vertexai=True, project=project_id, location=location
        )
        # 並列実行制御
        self._semaphore = asyncio.Semaphore(3)

    async def _translate_text(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """Gemini APIを使用してテキストを翻訳"""
        async with self._semaphore:
            return await self._translate_text_internal(text, target_language, context)

    async def _translate_text_internal(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """Gemini APIを使用してテキストを翻訳（内部実装）"""
        system_prompt = self._build_system_prompt(target_language)
        user_prompt = self._build_user_prompt(text, target_language, context)
        
        start_time = time.time()
        
        try:
            response = await self._client.aio.models.generate_content(
                model="gemini-2.5-flash-lite-preview-06-17",
                contents=[user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,  # 一貫性のために低温度設定
                    max_output_tokens=8192,
                ),
            )
            
            if response.text is None:
                self._logger.error("Empty response from Gemini API")
                return text
                
            elapsed_time = time.time() - start_time
            token_count = response.usage_metadata.total_token_count if response.usage_metadata else 0
            
            self._logger.info(
                "Gemini translation completed in %.2f seconds, %d tokens",
                elapsed_time,
                token_count
            )
            
            return response.text
            
        except Exception as e:
            self._logger.error("Gemini API error: %s", str(e))
            return text

    def _build_system_prompt(self, target_language: TargetLanguage) -> str:
        """Gemini向けのシステムプロンプト"""
        return f"""あなたは{target_language.value}のLaTeX翻訳専門家です。与えられたテキストを{target_language.value}に翻訳してください。

# 重要な規則:
1. LaTeXコマンド、環境、数式は一切変更しない
2. \\cite{{}}, \\ref{{}}, \\label{{}}内のキーは変更しない
3. 数式記号 $, \\(, \\), {{, }}, \\, &, % は絶対に変更しない
4. 自然言語部分のみを翻訳する
5. 文書構造を保持する
6. カスタムコマンドは翻訳しない
7. 空白やインデントを保持する
8. 学術的で自然な翻訳を心がける
9. 専門用語は適切な{target_language.value}訳語を使用する
10. 略語や固有名詞は適切に処理する

# 翻訳例:
入力: "This paper presents a novel approach to machine learning."
出力: "本論文では機械学習への新しいアプローチを提示する。"

# 禁止事項:
- コードブロック（```）で囲まない
- XMLタグを使用しない
- LaTeX構文の変更
- 全角文字の使用（数学記号以外）
- 不必要な説明や注釈の追加
- 翻訳結果以外の出力"""

    def _build_user_prompt(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """Gemini向けのユーザープロンプト"""
        prompt_parts = [
            f"翻訳対象言語: {target_language.value}",
        ]
        
        if context:
            prompt_parts.append(f"文書コンテキスト: {context}")
        
        prompt_parts.extend([
            "",
            "翻訳対象テキスト:",
            text,
            "",
            "上記テキストを指定言語に翻訳してください。翻訳結果のみを出力してください。"
        ])
        
        return "\n".join(prompt_parts)

    async def translate(self, latex_file, target_language):
        """並列処理でのセクション翻訳をサポート"""
        self._logger.info("Starting parallel translation of %s", latex_file.path)
        
        # 基本の翻訳処理を並列実行
        return await super().translate(latex_file, target_language)
