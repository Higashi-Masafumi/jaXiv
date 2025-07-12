from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from logging import getLogger
import re
import time

from domain.repositories import ILatexTranslator
from domain.entities import LatexFile, TargetLanguage
from utils.latex_parser import LatexParser, LatexElement, LatexElementType


class BaseLatexTranslator(ILatexTranslator, ABC):
    """LaTeX翻訳器のベースクラス"""

    def __init__(self, **kwargs):
        self._logger = getLogger(__name__)
        self._parser = LatexParser()
        self._init_specific(**kwargs)

    @abstractmethod
    def _init_specific(self, **kwargs):
        """サブクラス固有の初期化処理"""
        pass

    @abstractmethod
    async def _translate_text(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """テキストを翻訳する（サブクラスで実装）"""
        pass

    async def translate(self, latex_file: LatexFile, target_language: TargetLanguage) -> LatexFile:
        """LaTeX文書を翻訳する"""
        self._logger.info("Starting translation of %s", latex_file.path)
        
        # セクションごとに分割
        sections = self._parser.split_by_sections(latex_file.content)
        translated_sections = []
        
        for i, (section_title, section_content) in enumerate(sections):
            self._logger.info("Translating section %d: %s", i, section_title)
            
            if not section_content.strip():
                self._logger.warning("Empty section %d, skipping", i)
                translated_sections.append(section_content)
                continue
                
            try:
                translated_section = await self._translate_section(
                    section_content, target_language, section_title
                )
                translated_sections.append(translated_section)
            except Exception as e:
                self._logger.error("Failed to translate section %d: %s", i, str(e))
                # 翻訳失敗時は元のコンテンツを使用
                translated_sections.append(section_content)
        
        return LatexFile(
            path=latex_file.path,
            content="\n".join(translated_sections)
        )

    async def _translate_section(self, section_content: str, target_language: TargetLanguage, context: str = "") -> str:
        """セクションを翻訳する"""
        start_time = time.time()
        
        # LaTeX要素を解析
        elements = self._parser.parse(section_content)
        
        # 翻訳可能な要素を抽出
        translatable_elements = [elem for elem in elements if elem.should_translate and elem.type == LatexElementType.TEXT]
        
        if not translatable_elements:
            self._logger.info("No translatable text found in section")
            return section_content
        
        # 翻訳処理
        translated_elements = []
        for elem in translatable_elements:
            if elem.content.strip():  # 空白のみでない場合
                try:
                    translated_text = await self._translate_text(
                        elem.content.strip(), target_language, context
                    )
                    translated_elements.append((translated_text, elem.start_pos, elem.end_pos))
                except Exception as e:
                    self._logger.error("Failed to translate text element: %s", str(e))
                    translated_elements.append((elem.content, elem.start_pos, elem.end_pos))
        
        # 構造を保持して結果をマージ
        result = self._parser.preserve_structure(section_content, translated_elements)
        
        # 後処理
        result = self._post_process_translation(result)
        
        elapsed_time = time.time() - start_time
        self._logger.info("Section translated in %.2f seconds", elapsed_time)
        
        return result

    def _post_process_translation(self, translated_text: str) -> str:
        """翻訳後の後処理"""
        # AIの出力から不要なマークアップを除去
        cleaned_text = self._clean_ai_output(translated_text)
        
        # LaTeX固有の修正
        cleaned_text = self._fix_latex_syntax(cleaned_text)
        
        return cleaned_text

    def _clean_ai_output(self, text: str) -> str:
        """AIの出力から不要なマークアップを除去"""
        # コードブロックを除去
        text = re.sub(r'```(?:latex)?\s*(.*?)```', r'\1', text, flags=re.DOTALL)
        
        # XMLタグを除去
        text = re.sub(r'</?(?:latex|tex)>', '', text)
        
        # 余分な空行を調整
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def _fix_latex_syntax(self, text: str) -> str:
        """LaTeX構文の修正"""
        # 全角文字の修正
        replacements = {
            '（': '(',
            '）': ')',
            '｛': '{',
            '｝': '}',
            '［': '[',
            '］': ']',
            '＄': '$',
            '＼': '\\',
            '％': '%',
            '＆': '&',
            '＿': '_',
            '＾': '^',
            '｜': '|',
            '～': '~',
            '＃': '#',
        }
        
        for full_width, half_width in replacements.items():
            text = text.replace(full_width, half_width)
        
        # 数式内の空白を修正
        text = re.sub(r'\$\s+([^$]+)\s+\$', r'$\1$', text)
        
        # コマンドと引数の間の不要な空白を修正
        text = re.sub(r'\\([a-zA-Z]+)\s*\{', r'\\\1{', text)
        
        return text

    def _build_system_prompt(self, target_language: TargetLanguage) -> str:
        """システムプロンプトを構築"""
        return f"""あなたは{target_language.value}のLaTeX翻訳専門家です。与えられたLaTeXソースコードのテキスト部分のみを指定言語に翻訳してください。

# 重要な規則:
1. LaTeXコマンド、環境、数式は一切変更しない
2. \\cite{{}}, \\ref{{}}, \\label{{}}内のキーは変更しない
3. 数式記号 $, \\(, \\), {{, }}, \\, &, % は絶対に変更しない
4. 自然言語部分のみを翻訳する
5. 文書構造（\\begin{{document}}等）は保持する
6. カスタムコマンドは翻訳しない
7. 空白やインデントを保持する

# 翻訳例:
入力: \\section{{Introduction}}\\nThis paper studies...
出力: \\section{{はじめに}}\\n本論文では...を研究する。

# 禁止事項:
- コードブロック（```）で囲まない
- XMLタグ（<latex>）を使用しない
- LaTeX構文の変更
- 全角文字の使用（数学記号以外）"""

    def _build_user_prompt(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """ユーザープロンプトを構築"""
        prompt = f"翻訳対象言語: {target_language.value}\n"
        
        if context:
            prompt += f"コンテキスト: {context}\n"
        
        prompt += f"翻訳対象テキスト:\n{text}"
        
        return prompt

    def _estimate_tokens(self, text: str) -> int:
        """トークン数を推定"""
        # 簡易的な推定（実際の実装では各LLMの方式に合わせる）
        return len(text.split()) + len(re.findall(r'\\[a-zA-Z]+', text))

    def _should_split_content(self, content: str, max_tokens: int = 4000) -> bool:
        """コンテンツを分割すべきかどうかを判定"""
        return self._estimate_tokens(content) > max_tokens

    def _split_large_content(self, content: str, max_tokens: int = 4000) -> List[str]:
        """大きなコンテンツを分割"""
        if not self._should_split_content(content, max_tokens):
            return [content]
        
        # 段落単位で分割
        paragraphs = re.split(r'\n\s*\n', content)
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if self._estimate_tokens(current_chunk + paragraph) > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # 1段落が長すぎる場合は文単位で分割
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    for sentence in sentences:
                        if self._estimate_tokens(current_chunk + sentence) > max_tokens:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = sentence
                            else:
                                chunks.append(sentence)
                        else:
                            current_chunk += " " + sentence if current_chunk else sentence
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks