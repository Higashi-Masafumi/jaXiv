from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from logging import getLogger
import re
import time
import tempfile
from pathlib import Path

from domain.repositories import ILatexTranslator
from domain.entities import LatexFile, TargetLanguage
from utils.latex_parser import LatexParser, LatexElement, LatexElementType
from utils.latex_project_analyzer import LatexProjectAnalyzer
from utils.latex_validator import LatexValidator


class BaseLatexTranslator(ILatexTranslator, ABC):
    """LaTeX翻訳器のベースクラス"""

    def __init__(self, **kwargs):
        self._logger = getLogger(__name__)
        self._parser = LatexParser()
        self._project_analyzer: Optional[LatexProjectAnalyzer] = None
        self._validator: Optional[LatexValidator] = None
        self._init_specific(**kwargs)

    @abstractmethod
    def _init_specific(self, **kwargs):
        """サブクラス固有の初期化処理"""
        pass

    @abstractmethod
    async def _translate_text(self, text: str, target_language: TargetLanguage, context: str = "") -> str:
        """テキストを翻訳する（サブクラスで実装）"""
        pass

    def set_project_context(self, project_root: str):
        """プロジェクトコンテキストを設定"""
        self._project_analyzer = LatexProjectAnalyzer(project_root)
        self._project_analyzer.analyze_project()
        self._validator = LatexValidator(self._project_analyzer)
        
        # プロジェクトの検証を実行
        validation_result = self._validator.validate_project()
        self._logger.info(f"Project validation: {validation_result['error_count']} errors, {validation_result['warning_count']} warnings")
        
        # コンパイル可能性をテスト
        if validation_result['is_compilable']:
            compilation_result = self._validator.test_compilation()
            if compilation_result['success']:
                self._logger.info("Project compilation test passed")
            else:
                self._logger.warning(f"Project compilation test failed: {compilation_result['error']}")

    async def translate(self, latex_file: LatexFile, target_language: TargetLanguage) -> LatexFile:
        """LaTeX文書を翻訳する"""
        self._logger.info("Starting translation of %s", latex_file.path)
        
        # プロジェクトコンテキストが設定されている場合は高度な翻訳を実行
        if self._project_analyzer and self._validator:
            return await self._translate_with_project_context(latex_file, target_language)
        else:
            return await self._translate_basic(latex_file, target_language)

    async def _translate_with_project_context(self, latex_file: LatexFile, target_language: TargetLanguage) -> LatexFile:
        """プロジェクトコンテキストを使用した高度な翻訳"""
        self._logger.info("Using project-aware translation for %s", latex_file.path)
        
        # プロジェクトに追加（既存でない場合）
        if self._project_analyzer and latex_file.path not in self._project_analyzer.files:
            self._project_analyzer.files[latex_file.path] = latex_file
        
        # コンパイル安全なコンテキストを取得
        context = self._validator.get_compilation_safe_context(latex_file.path) if self._validator else {}
        
        # 翻訳前の自動修正
        auto_fixes = self._validator.auto_fix_issues() if self._validator else {}
        if latex_file.path in auto_fixes:
            latex_file.content = auto_fixes[latex_file.path]
            self._logger.info("Applied auto-fixes to %s", latex_file.path)
        
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
                # 翻訳コンテキストを構築
                section_context = self._build_enhanced_context(context, section_title, section_content)
                
                translated_section = await self._translate_section_with_context(
                    section_content, target_language, section_context
                )
                translated_sections.append(translated_section)
            except Exception as e:
                self._logger.error("Failed to translate section %d: %s", i, str(e))
                # 翻訳失敗時は元のコンテンツを使用
                translated_sections.append(section_content)
        
        translated_content = "\n".join(translated_sections)
        
        # 翻訳後の検証
        translated_file = LatexFile(path=latex_file.path, content=translated_content)
        await self._validate_translated_content(translated_file, target_language)
        
        return translated_file

    async def _translate_basic(self, latex_file: LatexFile, target_language: TargetLanguage) -> LatexFile:
        """基本的な翻訳（プロジェクトコンテキストなし）"""
        self._logger.info("Using basic translation for %s", latex_file.path)
        
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

    async def _translate_section_with_context(self, section_content: str, target_language: TargetLanguage, context: Dict[str, Any]) -> str:
        """コンテキストを使用したセクション翻訳"""
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
                    # 強化されたコンテキストを使用
                    enhanced_context = self._build_element_context(context, elem)
                    translated_text = await self._translate_text(
                        elem.content.strip(), target_language, enhanced_context
                    )
                    translated_elements.append((translated_text, elem.start_pos, elem.end_pos))
                except Exception as e:
                    self._logger.error("Failed to translate text element: %s", str(e))
                    translated_elements.append((elem.content, elem.start_pos, elem.end_pos))
        
        # 構造を保持して結果をマージ
        result = self._parser.preserve_structure(section_content, translated_elements)
        
        # 後処理
        result = self._post_process_translation(result)
        
        # 追加の検証
        if self._validator:
            result = self._validate_translation_result(result, section_content)
        
        elapsed_time = time.time() - start_time
        self._logger.info("Section translated in %.2f seconds", elapsed_time)
        
        return result

    async def _translate_section(self, section_content: str, target_language: TargetLanguage, context: str = "") -> str:
        """基本的なセクション翻訳"""
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

    def _build_enhanced_context(self, project_context: Dict[str, Any], section_title: str, section_content: str) -> Dict[str, Any]:
        """強化されたコンテキストを構築"""
        enhanced_context = {
            'project_context': project_context,
            'section_title': section_title,
            'content_preview': section_content[:200] + "..." if len(section_content) > 200 else section_content,
            'critical_commands': project_context.get('critical_commands', []),
            'safe_translation_rules': project_context.get('safe_translation_rules', []),
            'custom_commands': project_context.get('custom_commands', {}),
            'custom_environments': project_context.get('custom_environments', {}),
        }
        return enhanced_context

    def _build_element_context(self, section_context: Dict[str, Any], element: LatexElement) -> str:
        """要素固有のコンテキストを構築"""
        context_parts = []
        
        # プロジェクトコンテキスト
        if section_context.get('project_context'):
            context_parts.append("プロジェクトコンテキスト: LaTeX学術論文の翻訳")
        
        # セクション情報
        if section_context.get('section_title'):
            context_parts.append(f"セクション: {section_context['section_title']}")
        
        # 重要なコマンド
        if section_context.get('critical_commands'):
            context_parts.append(f"重要なコマンド: {', '.join(section_context['critical_commands'])}")
        
        # 翻訳ルール
        if section_context.get('safe_translation_rules'):
            context_parts.append("翻訳ルール:")
            for rule in section_context['safe_translation_rules']:
                context_parts.append(f"- {rule}")
        
        return "\n".join(context_parts)

    async def _validate_translated_content(self, translated_file: LatexFile, target_language: TargetLanguage):
        """翻訳後の内容を検証"""
        if not self._validator:
            return
        
        # 一時的にファイルを更新して検証
        if not self._project_analyzer or not self._validator:
            return
            
        original_content = self._project_analyzer.files[translated_file.path].content
        self._project_analyzer.files[translated_file.path].content = translated_file.content
        
        try:
            # 検証実行
            validation_result = self._validator.validate_project()
            
            # 新しいエラーが発生した場合は警告
            if validation_result['error_count'] > 0:
                self._logger.warning(f"Translation introduced {validation_result['error_count']} validation errors")
                
                # 重要なエラーがある場合は自動修正を試行
                auto_fixes = self._validator.auto_fix_issues()
                if translated_file.path in auto_fixes:
                    translated_file.content = auto_fixes[translated_file.path]
                    self._logger.info("Applied auto-fixes to translated content")
        
        finally:
            # 元の内容を復元
            self._project_analyzer.files[translated_file.path].content = original_content

    def _validate_translation_result(self, translated_result: str, original_content: str) -> str:
        """翻訳結果の検証と修正"""
        # 基本的な構造チェック
        original_commands = re.findall(r'\\([a-zA-Z]+)', original_content)
        translated_commands = re.findall(r'\\([a-zA-Z]+)', translated_result)
        
        # コマンドの数が大幅に変わった場合は警告
        if abs(len(original_commands) - len(translated_commands)) > len(original_commands) * 0.1:
            self._logger.warning("Translation may have corrupted LaTeX commands")
        
        # 数式の数をチェック
        original_math = len(re.findall(r'\$[^$]+\$', original_content))
        translated_math = len(re.findall(r'\$[^$]+\$', translated_result))
        
        if original_math != translated_math:
            self._logger.warning("Math expression count mismatch after translation")
        
        return translated_result

    def _post_process_translation(self, translated_text: str) -> str:
        """翻訳後の後処理"""
        # AIの出力から不要なマークアップを除去
        cleaned_text = self._clean_ai_output(translated_text)
        
        # LaTeX固有の修正
        cleaned_text = self._fix_latex_syntax(cleaned_text)
        
        # 追加の構造チェック
        cleaned_text = self._ensure_structure_integrity(cleaned_text)
        
        return cleaned_text

    def _ensure_structure_integrity(self, text: str) -> str:
        """構造の整合性を確保"""
        # 括弧の対応をチェック
        open_braces = text.count('{')
        close_braces = text.count('}')
        
        if open_braces != close_braces:
            self._logger.warning(f"Brace mismatch: {open_braces} open, {close_braces} close")
        
        # 数式記号の対応をチェック
        math_delimiters = text.count('$')
        if math_delimiters % 2 != 0:
            self._logger.warning("Unmatched math delimiters")
        
        return text

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