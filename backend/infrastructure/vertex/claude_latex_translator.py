from anthropic import AnthropicVertex
from anthropic.types import TextBlock
from domain.entities import TargetLanguage
from utils.latex_translator_base import BaseLatexTranslator


class ClaudeLatexTranslator(BaseLatexTranslator):
    """Claude Sonnet を使用したLaTeX翻訳器"""

    def _init_specific(self, project_id: str, location: str, model_name: str = "claude-3-5-sonnet-20241022"):
        """Claude固有の初期化"""
        self._project_id = project_id
        self._location = location
        self._model_name = model_name
        self._client = AnthropicVertex(project_id=project_id, region=location)

    async def _translate_text(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """Claude APIを使用してテキストを翻訳"""
        system_prompt = self._build_system_prompt(target_language)
        user_prompt = self._build_user_prompt(text, target_language, context)
        
        try:
            response = self._client.messages.create(
                model=self._model_name,
                system=system_prompt,
                max_tokens=8192,
                temperature=0.1,  # 一貫性のために低温度設定
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )
            
            if response.content and len(response.content) > 0:
                content_block = response.content[0]
                if isinstance(content_block, TextBlock):
                    return content_block.text
                else:
                    self._logger.error("Unexpected content type in response")
                    return text
            else:
                self._logger.error("Empty response content")
                return text
                
        except Exception as e:
            self._logger.error("Claude API error: %s", str(e))
            return text

    def _build_system_prompt(self, target_language: TargetLanguage) -> str:
        """Claude向けのシステムプロンプト"""
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

# 翻訳例:
入力: "This paper presents a novel approach to machine learning."
出力: "本論文では機械学習への新しいアプローチを提示する。"

# 禁止事項:
- コードブロック（```）で囲まない
- XMLタグを使用しない
- LaTeX構文の変更
- 全角文字の使用（数学記号以外）
- 不必要な説明や注釈の追加"""

    def _build_user_prompt(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """Claude向けのユーザープロンプト"""
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
