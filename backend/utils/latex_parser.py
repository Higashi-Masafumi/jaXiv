import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class LatexElementType(Enum):
    """LaTeX要素の種類"""
    TEXT = "text"
    MATH_INLINE = "math_inline"
    MATH_DISPLAY = "math_display"
    COMMAND = "command"
    ENVIRONMENT = "environment"
    COMMENT = "comment"
    CITATION = "citation"
    REFERENCE = "reference"
    LABEL = "label"


@dataclass
class LatexElement:
    """LaTeX要素を表すデータクラス"""
    type: LatexElementType
    content: str
    start_pos: int
    end_pos: int
    should_translate: bool = True
    metadata: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LatexParser:
    """LaTeX文書の高度な解析を行うクラス"""
    
    # 翻訳対象外のコマンド
    NON_TRANSLATABLE_COMMANDS = {
        'cite', 'ref', 'label', 'includegraphics', 'input', 'include',
        'documentclass', 'usepackage', 'newcommand', 'renewcommand',
        'def', 'let', 'url', 'href', 'hyperref', 'pageref', 'autoref',
        'nameref', 'eqref', 'cref', 'Cref'
    }
    
    # 翻訳対象外の環境
    NON_TRANSLATABLE_ENVIRONMENTS = {
        'equation', 'align', 'gather', 'multline', 'flalign', 'alignat',
        'eqnarray', 'displaymath', 'verbatim', 'lstlisting', 'minted',
        'algorithm', 'algorithmic', 'tikzpicture', 'pgfpicture'
    }
    
    # セクション系コマンド（重要度順）
    SECTION_COMMANDS = [
        'part', 'chapter', 'section', 'subsection', 
        'subsubsection', 'paragraph', 'subparagraph'
    ]

    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """正規表現パターンをコンパイル"""
        # 数式パターン
        self.math_inline_pattern = re.compile(r'\$([^$]+)\$')
        self.math_display_pattern = re.compile(r'\$\$([^$]+)\$\$|\\\[(.*?)\\\]', re.DOTALL)
        
        # コマンドパターン
        self.command_pattern = re.compile(r'\\([a-zA-Z]+)(\*?)(\[.*?\])?({.*?})*')
        
        # 環境パターン
        self.environment_pattern = re.compile(r'\\begin\{([^}]+)\}(.*?)\\end\{\1\}', re.DOTALL)
        
        # 引用・参照パターン
        self.citation_pattern = re.compile(r'\\cite\*?(?:\[.*?\])?\{([^}]+)\}')
        self.reference_pattern = re.compile(r'\\(?:ref|pageref|autoref|nameref|eqref|cref|Cref)\*?\{([^}]+)\}')
        self.label_pattern = re.compile(r'\\label\{([^}]+)\}')
        
        # コメントパターン
        self.comment_pattern = re.compile(r'(?<!\\)%.*$', re.MULTILINE)
        
        # セクションパターン
        section_pattern = '|'.join(self.SECTION_COMMANDS)
        self.section_pattern = re.compile(rf'^\\({section_pattern})(\*?)(\[.*?\])?\{{([^}}]+)\}}', re.MULTILINE)

    def parse(self, latex_content: str) -> List[LatexElement]:
        """LaTeX文書を解析して要素リストを返す"""
        elements = []
        
        # 各種要素を検出
        elements.extend(self._find_math_elements(latex_content))
        elements.extend(self._find_environments(latex_content))
        elements.extend(self._find_commands(latex_content))
        elements.extend(self._find_citations_and_references(latex_content))
        elements.extend(self._find_comments(latex_content))
        
        # 位置でソート
        elements.sort(key=lambda x: x.start_pos)
        
        # テキスト部分を補完
        elements = self._fill_text_elements(latex_content, elements)
        
        return elements

    def _find_math_elements(self, content: str) -> List[LatexElement]:
        """数式要素を検出"""
        elements = []
        
        # ディスプレイ数式
        for match in self.math_display_pattern.finditer(content):
            elements.append(LatexElement(
                type=LatexElementType.MATH_DISPLAY,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=False
            ))
        
        # インライン数式
        for match in self.math_inline_pattern.finditer(content):
            # ディスプレイ数式と重複しないかチェック
            if not any(elem.start_pos <= match.start() < elem.end_pos 
                      for elem in elements if elem.type == LatexElementType.MATH_DISPLAY):
                elements.append(LatexElement(
                    type=LatexElementType.MATH_INLINE,
                    content=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    should_translate=False
                ))
        
        return elements

    def _find_environments(self, content: str) -> List[LatexElement]:
        """環境要素を検出"""
        elements = []
        
        for match in self.environment_pattern.finditer(content):
            env_name = match.group(1)
            should_translate = env_name not in self.NON_TRANSLATABLE_ENVIRONMENTS
            
            elements.append(LatexElement(
                type=LatexElementType.ENVIRONMENT,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=should_translate,
                metadata={'environment': env_name}
            ))
        
        return elements

    def _find_commands(self, content: str) -> List[LatexElement]:
        """コマンド要素を検出"""
        elements = []
        
        for match in self.command_pattern.finditer(content):
            command_name = match.group(1)
            should_translate = command_name not in self.NON_TRANSLATABLE_COMMANDS
            
            elements.append(LatexElement(
                type=LatexElementType.COMMAND,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=should_translate,
                metadata={'command': command_name}
            ))
        
        return elements

    def _find_citations_and_references(self, content: str) -> List[LatexElement]:
        """引用・参照要素を検出"""
        elements = []
        
        # 引用
        for match in self.citation_pattern.finditer(content):
            elements.append(LatexElement(
                type=LatexElementType.CITATION,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=False,
                metadata={'keys': match.group(1)}
            ))
        
        # 参照
        for match in self.reference_pattern.finditer(content):
            elements.append(LatexElement(
                type=LatexElementType.REFERENCE,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=False,
                metadata={'key': match.group(1)}
            ))
        
        # ラベル
        for match in self.label_pattern.finditer(content):
            elements.append(LatexElement(
                type=LatexElementType.LABEL,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=False,
                metadata={'key': match.group(1)}
            ))
        
        return elements

    def _find_comments(self, content: str) -> List[LatexElement]:
        """コメント要素を検出"""
        elements = []
        
        for match in self.comment_pattern.finditer(content):
            elements.append(LatexElement(
                type=LatexElementType.COMMENT,
                content=match.group(0),
                start_pos=match.start(),
                end_pos=match.end(),
                should_translate=False
            ))
        
        return elements

    def _fill_text_elements(self, content: str, elements: List[LatexElement]) -> List[LatexElement]:
        """テキスト部分を補完"""
        if not elements:
            return [LatexElement(
                type=LatexElementType.TEXT,
                content=content,
                start_pos=0,
                end_pos=len(content),
                should_translate=True
            )]
        
        result = []
        last_end = 0
        
        for elem in elements:
            # 前の要素との間にテキストがあれば追加
            if elem.start_pos > last_end:
                text_content = content[last_end:elem.start_pos]
                if text_content.strip():  # 空白のみでない場合
                    result.append(LatexElement(
                        type=LatexElementType.TEXT,
                        content=text_content,
                        start_pos=last_end,
                        end_pos=elem.start_pos,
                        should_translate=True
                    ))
            
            result.append(elem)
            last_end = elem.end_pos
        
        # 最後の要素以降にテキストがあれば追加
        if last_end < len(content):
            text_content = content[last_end:]
            if text_content.strip():
                result.append(LatexElement(
                    type=LatexElementType.TEXT,
                    content=text_content,
                    start_pos=last_end,
                    end_pos=len(content),
                    should_translate=True
                ))
        
        return result

    def split_by_sections(self, latex_content: str) -> List[Tuple[str, str]]:
        """セクションで分割（セクションタイトルと内容のタプルを返す）"""
        sections = []
        matches = list(self.section_pattern.finditer(latex_content))
        
        if not matches:
            return [("", latex_content)]
        
        # セクション前の内容
        if matches[0].start() > 0:
            pre_content = latex_content[:matches[0].start()].strip()
            if pre_content:
                sections.append(("", pre_content))
        
        # 各セクション
        for i, match in enumerate(matches):
            section_command = match.group(1)
            section_title = match.group(4)
            
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(latex_content)
            
            section_content = latex_content[start_pos:end_pos].strip()
            sections.append((f"{section_command}: {section_title}", section_content))
        
        return sections

    def extract_translatable_text(self, latex_content: str) -> List[Tuple[str, int, int]]:
        """翻訳可能なテキスト部分を抽出"""
        elements = self.parse(latex_content)
        translatable_parts = []
        
        for elem in elements:
            if elem.should_translate and elem.type == LatexElementType.TEXT:
                # 空白のみでない場合のみ追加
                if elem.content.strip():
                    translatable_parts.append((elem.content, elem.start_pos, elem.end_pos))
        
        return translatable_parts

    def preserve_structure(self, original: str, translated_parts: List[Tuple[str, int, int]]) -> str:
        """構造を保持して翻訳結果をマージ"""
        if not translated_parts:
            return original
        
        result = []
        last_end = 0
        
        for translated_text, start_pos, end_pos in translated_parts:
            # 変更されない部分を追加
            if start_pos > last_end:
                result.append(original[last_end:start_pos])
            
            # 翻訳された部分を追加
            result.append(translated_text)
            last_end = end_pos
        
        # 最後の部分を追加
        if last_end < len(original):
            result.append(original[last_end:])
        
        return ''.join(result)