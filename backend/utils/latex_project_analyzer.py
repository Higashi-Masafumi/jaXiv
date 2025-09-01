import os
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from logging import getLogger

from .latex_parser import LatexParser, LatexElement, LatexElementType


@dataclass
class LatexCommand:
    """LaTeXコマンドの定義"""
    name: str
    definition: str
    num_args: int = 0
    optional_args: int = 0
    is_custom: bool = True
    source_file: Optional[str] = None


@dataclass
class LatexEnvironment:
    """LaTeX環境の定義"""
    name: str
    definition: str
    is_custom: bool = True
    source_file: Optional[str] = None


@dataclass
class LatexFile:
    """LaTeXファイルの情報"""
    path: str
    content: str
    dependencies: List[str] = field(default_factory=list)
    custom_commands: List[LatexCommand] = field(default_factory=list)
    custom_environments: List[LatexEnvironment] = field(default_factory=list)
    used_commands: Set[str] = field(default_factory=set)
    used_environments: Set[str] = field(default_factory=set)
    citations: Set[str] = field(default_factory=set)
    labels: Set[str] = field(default_factory=set)
    refs: Set[str] = field(default_factory=set)


class LatexProjectAnalyzer:
    """LaTeXプロジェクト全体の解析と依存関係管理"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = getLogger(__name__)
        self.parser = LatexParser()
        
        # プロジェクト情報
        self.main_file: Optional[str] = None
        self.files: Dict[str, LatexFile] = {}
        self.global_commands: Dict[str, LatexCommand] = {}
        self.global_environments: Dict[str, LatexEnvironment] = {}
        
        # 標準LaTeXコマンド/環境
        self.standard_commands = self._load_standard_commands()
        self.standard_environments = self._load_standard_environments()
        
        # 分析結果
        self.dependency_graph: Dict[str, List[str]] = {}
        self.compilation_order: List[str] = []

    def analyze_project(self) -> Dict[str, Any]:
        """プロジェクト全体を解析"""
        self.logger.info("Starting LaTeX project analysis")
        
        # 1. LaTeXファイルを発見
        latex_files = self._find_latex_files()
        self.logger.info(f"Found {len(latex_files)} LaTeX files")
        
        # 2. メインファイルを特定
        self.main_file = self._find_main_file(latex_files)
        self.logger.info(f"Main file: {self.main_file}")
        
        # 3. 各ファイルを解析
        for file_path in latex_files:
            self._analyze_file(file_path)
        
        # 4. 依存関係を構築
        self._build_dependency_graph()
        
        # 5. コンパイル順序を決定
        self.compilation_order = self._determine_compilation_order()
        
        # 6. グローバルコマンド/環境を統合
        self._integrate_global_definitions()
        
        analysis_result = {
            'main_file': self.main_file,
            'files': self.files,
            'global_commands': self.global_commands,
            'global_environments': self.global_environments,
            'dependency_graph': self.dependency_graph,
            'compilation_order': self.compilation_order,
            'project_structure': self._get_project_structure()
        }
        
        self.logger.info("Project analysis completed")
        return analysis_result

    def _find_latex_files(self) -> List[str]:
        """LaTeXファイルを発見"""
        latex_files = []
        for ext in ['.tex', '.latex']:
            latex_files.extend(self.project_root.glob(f"**/*{ext}"))
        return [str(f.relative_to(self.project_root)) for f in latex_files]

    def _find_main_file(self, latex_files: List[str]) -> Optional[str]:
        """メインファイルを特定"""
        # 1. main.tex, paper.tex, document.tex などの一般的な名前
        common_names = ['main.tex', 'paper.tex', 'document.tex', 'thesis.tex', 'article.tex']
        for name in common_names:
            if name in latex_files:
                return name
        
        # 2. \documentclass を含むファイル
        for file_path in latex_files:
            try:
                with open(self.project_root / file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(r'\\documentclass', content):
                        return file_path
            except Exception as e:
                self.logger.warning(f"Error reading {file_path}: {e}")
        
        # 3. 最初のファイルをデフォルトとする
        return latex_files[0] if latex_files else None

    def _analyze_file(self, file_path: str) -> LatexFile:
        """個別ファイルを解析"""
        full_path = self.project_root / file_path
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            content = ""
        
        latex_file = LatexFile(path=file_path, content=content)
        
        # LaTeX要素を解析
        elements = self.parser.parse(content)
        
        # 各要素を分析
        for element in elements:
            if element.type == LatexElementType.COMMAND:
                self._analyze_command(element, latex_file)
            elif element.type == LatexElementType.ENVIRONMENT:
                self._analyze_environment(element, latex_file)
            elif element.type == LatexElementType.CITATION:
                self._analyze_citation(element, latex_file)
            elif element.type == LatexElementType.REFERENCE:
                self._analyze_reference(element, latex_file)
            elif element.type == LatexElementType.LABEL:
                self._analyze_label(element, latex_file)
        
        # 依存関係を解析
        self._analyze_dependencies(content, latex_file)
        
        # カスタムコマンド/環境の定義を解析
        self._analyze_custom_definitions(content, latex_file)
        
        self.files[file_path] = latex_file
        return latex_file

    def _analyze_command(self, element: LatexElement, latex_file: LatexFile):
        """コマンドを解析"""
        if element.metadata and 'command' in element.metadata:
            command_name = element.metadata['command']
            latex_file.used_commands.add(command_name)

    def _analyze_environment(self, element: LatexElement, latex_file: LatexFile):
        """環境を解析"""
        if element.metadata and 'environment' in element.metadata:
            env_name = element.metadata['environment']
            latex_file.used_environments.add(env_name)

    def _analyze_citation(self, element: LatexElement, latex_file: LatexFile):
        """引用を解析"""
        if element.metadata and 'keys' in element.metadata:
            keys = element.metadata['keys'].split(',')
            for key in keys:
                latex_file.citations.add(key.strip())

    def _analyze_reference(self, element: LatexElement, latex_file: LatexFile):
        """参照を解析"""
        if element.metadata and 'key' in element.metadata:
            latex_file.refs.add(element.metadata['key'])

    def _analyze_label(self, element: LatexElement, latex_file: LatexFile):
        """ラベルを解析"""
        if element.metadata and 'key' in element.metadata:
            latex_file.labels.add(element.metadata['key'])

    def _analyze_dependencies(self, content: str, latex_file: LatexFile):
        """依存関係を解析"""
        # \input, \include, \subfile などを検出
        patterns = [
            r'\\input\{([^}]+)\}',
            r'\\include\{([^}]+)\}',
            r'\\subfile\{([^}]+)\}',
            r'\\InputIfFileExists\{([^}]+)\}',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                dep_file = match.group(1)
                if not dep_file.endswith('.tex'):
                    dep_file += '.tex'
                latex_file.dependencies.append(dep_file)

    def _analyze_custom_definitions(self, content: str, latex_file: LatexFile):
        """カスタムコマンド/環境の定義を解析"""
        # \newcommand, \renewcommand
        command_patterns = [
            r'\\newcommand\{\\([^}]+)\}(?:\[(\d+)\])?\{([^}]+)\}',
            r'\\renewcommand\{\\([^}]+)\}(?:\[(\d+)\])?\{([^}]+)\}',
            r'\\def\\([^{]+)\{([^}]+)\}',
        ]
        
        for pattern in command_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                cmd_name = match.group(1)
                num_args = int(match.group(2)) if match.group(2) else 0
                definition = match.group(3) if len(match.groups()) > 2 else match.group(2)
                
                command = LatexCommand(
                    name=cmd_name,
                    definition=definition,
                    num_args=num_args,
                    source_file=latex_file.path
                )
                latex_file.custom_commands.append(command)
        
        # \newenvironment, \renewenvironment
        env_patterns = [
            r'\\newenvironment\{([^}]+)\}(?:\[(\d+)\])?\{([^}]+)\}\{([^}]+)\}',
            r'\\renewenvironment\{([^}]+)\}(?:\[(\d+)\])?\{([^}]+)\}\{([^}]+)\}',
        ]
        
        for pattern in env_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                env_name = match.group(1)
                begin_def = match.group(3)
                end_def = match.group(4)
                definition = f"\\begin{{{env_name}}}{begin_def}...\\end{{{env_name}}}{end_def}"
                
                environment = LatexEnvironment(
                    name=env_name,
                    definition=definition,
                    source_file=latex_file.path
                )
                latex_file.custom_environments.append(environment)

    def _build_dependency_graph(self):
        """依存関係グラフを構築"""
        for file_path, latex_file in self.files.items():
            self.dependency_graph[file_path] = []
            for dep in latex_file.dependencies:
                if dep in self.files:
                    self.dependency_graph[file_path].append(dep)

    def _determine_compilation_order(self) -> List[str]:
        """コンパイル順序を決定（トポロジカルソート）"""
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(node):
            if node in temp_visited:
                return  # 循環依存を検出
            if node in visited:
                return
            
            temp_visited.add(node)
            for dep in self.dependency_graph.get(node, []):
                visit(dep)
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        for file_path in self.files:
            if file_path not in visited:
                visit(file_path)
        
        return result

    def _integrate_global_definitions(self):
        """グローバルコマンド/環境定義を統合"""
        for latex_file in self.files.values():
            for command in latex_file.custom_commands:
                self.global_commands[command.name] = command
            for environment in latex_file.custom_environments:
                self.global_environments[environment.name] = environment

    def _get_project_structure(self) -> Dict[str, Any]:
        """プロジェクト構造を取得"""
        return {
            'total_files': len(self.files),
            'main_file': self.main_file,
            'custom_commands': len(self.global_commands),
            'custom_environments': len(self.global_environments),
            'dependency_depth': max(len(deps) for deps in self.dependency_graph.values()) if self.dependency_graph else 0,
        }

    def _load_standard_commands(self) -> Set[str]:
        """標準LaTeXコマンドを読み込み"""
        return {
            'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph',
            'chapter', 'part', 'title', 'author', 'date', 'maketitle',
            'tableofcontents', 'listoffigures', 'listoftables',
            'textbf', 'textit', 'textsc', 'texttt', 'emph', 'underline',
            'footnote', 'marginpar', 'caption', 'label', 'ref', 'pageref',
            'cite', 'bibliography', 'bibliographystyle',
            'begin', 'end', 'item', 'enumerate', 'itemize', 'description',
            'figure', 'table', 'center', 'flushleft', 'flushright',
            'includegraphics', 'usepackage', 'documentclass',
            'newpage', 'clearpage', 'pagebreak', 'linebreak',
            'hspace', 'vspace', 'quad', 'qquad',
        }

    def _load_standard_environments(self) -> Set[str]:
        """標準LaTeX環境を読み込み"""
        return {
            'document', 'abstract', 'quote', 'quotation', 'verse',
            'itemize', 'enumerate', 'description', 'list',
            'figure', 'table', 'tabular', 'array',
            'equation', 'align', 'gather', 'multline', 'split',
            'eqnarray', 'displaymath', 'math',
            'center', 'flushleft', 'flushright',
            'minipage', 'parbox', 'makebox', 'framebox',
            'verbatim', 'verbatim*', 'verse',
            'thebibliography', 'theindex',
        }

    def validate_references(self) -> Dict[str, List[str]]:
        """参照の整合性をチェック"""
        issues = {'missing_labels': [], 'missing_citations': []}
        
        # 全てのラベルを収集
        all_labels = set()
        for latex_file in self.files.values():
            all_labels.update(latex_file.labels)
        
        # 未定義参照をチェック
        for latex_file in self.files.values():
            for ref in latex_file.refs:
                if ref not in all_labels:
                    issues['missing_labels'].append(f"{latex_file.path}: \\ref{{{ref}}}")
        
        return issues

    def get_translation_context(self, file_path: str) -> Dict[str, Any]:
        """翻訳用のコンテキスト情報を取得"""
        if file_path not in self.files:
            return {}
        
        latex_file = self.files[file_path]
        
        # 利用可能なコマンドを収集
        available_commands = set(self.standard_commands)
        available_commands.update(self.global_commands.keys())
        
        # 利用可能な環境を収集
        available_environments = set(self.standard_environments)
        available_environments.update(self.global_environments.keys())
        
        return {
            'file_path': file_path,
            'is_main_file': file_path == self.main_file,
            'dependencies': latex_file.dependencies,
            'available_commands': list(available_commands),
            'available_environments': list(available_environments),
            'custom_commands': {cmd.name: cmd.definition for cmd in latex_file.custom_commands},
            'custom_environments': {env.name: env.definition for env in latex_file.custom_environments},
            'used_commands': list(latex_file.used_commands),
            'used_environments': list(latex_file.used_environments),
            'labels': list(latex_file.labels),
            'citations': list(latex_file.citations),
            'refs': list(latex_file.refs),
        }