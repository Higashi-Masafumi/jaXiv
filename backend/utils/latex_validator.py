import re
import tempfile
import subprocess
from typing import Dict, List, Tuple, Optional, Set, Any
from pathlib import Path
from logging import getLogger
from dataclasses import dataclass

from .latex_parser import LatexParser
from .latex_project_analyzer import LatexProjectAnalyzer, LatexFile


@dataclass
class ValidationIssue:
    """検証で発見された問題"""
    type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class LatexValidator:
    """LaTeX文書の検証とコンパイル可能性チェック"""
    
    def __init__(self, project_analyzer: LatexProjectAnalyzer):
        self.analyzer = project_analyzer
        self.logger = getLogger(__name__)
        self.parser = LatexParser()
        
        # 検証結果
        self.issues: List[ValidationIssue] = []
        self.fixes_applied: List[str] = []

    def validate_project(self) -> Dict[str, Any]:
        """プロジェクト全体の検証"""
        self.issues = []
        self.fixes_applied = []
        
        self.logger.info("Starting LaTeX project validation")
        
        # 1. 基本構造の検証
        self._validate_project_structure()
        
        # 2. 個別ファイルの検証
        for file_path, latex_file in self.analyzer.files.items():
            self._validate_file(latex_file)
        
        # 3. 依存関係の検証
        self._validate_dependencies()
        
        # 4. 参照の整合性検証
        self._validate_references()
        
        # 5. カスタムコマンド/環境の検証
        self._validate_custom_definitions()
        
        # 6. 文法チェック
        self._validate_latex_syntax()
        
        result = {
            'issues': self.issues,
            'fixes_applied': self.fixes_applied,
            'error_count': len([i for i in self.issues if i.severity == 'error']),
            'warning_count': len([i for i in self.issues if i.severity == 'warning']),
            'is_compilable': len([i for i in self.issues if i.severity == 'error']) == 0,
        }
        
        self.logger.info(f"Validation completed: {result['error_count']} errors, {result['warning_count']} warnings")
        return result

    def _validate_project_structure(self):
        """プロジェクト構造の検証"""
        if not self.analyzer.main_file:
            self.issues.append(ValidationIssue(
                type="missing_main_file",
                severity="error",
                message="メインファイルが見つかりません",
                file_path="",
                suggestion="main.tex または documentclass を含むファイルを作成してください"
            ))
            return
        
        main_file = self.analyzer.files[self.analyzer.main_file]
        if not re.search(r'\\documentclass', main_file.content):
            self.issues.append(ValidationIssue(
                type="missing_documentclass",
                severity="error",
                message="\\documentclass が見つかりません",
                file_path=self.analyzer.main_file,
                suggestion="\\documentclass{article} などを追加してください"
            ))
        
        if not re.search(r'\\begin\{document\}', main_file.content):
            self.issues.append(ValidationIssue(
                type="missing_begin_document",
                severity="error",
                message="\\begin{document} が見つかりません",
                file_path=self.analyzer.main_file,
                suggestion="\\begin{document} を追加してください"
            ))
        
        if not re.search(r'\\end\{document\}', main_file.content):
            self.issues.append(ValidationIssue(
                type="missing_end_document",
                severity="error",
                message="\\end{document} が見つかりません",
                file_path=self.analyzer.main_file,
                suggestion="\\end{document} を追加してください"
            ))

    def _validate_file(self, latex_file: LatexFile):
        """個別ファイルの検証"""
        content = latex_file.content
        lines = content.split('\n')
        
        # 基本的な文法チェック
        for i, line in enumerate(lines, 1):
            # 未閉じの括弧チェック
            if line.count('{') != line.count('}'):
                self.issues.append(ValidationIssue(
                    type="unmatched_braces",
                    severity="warning",
                    message=f"括弧が一致しません: {line.strip()}",
                    file_path=latex_file.path,
                    line_number=i,
                    suggestion="括弧の数を確認してください"
                ))
            
            # 未閉じの数式チェック
            if line.count('$') % 2 != 0:
                self.issues.append(ValidationIssue(
                    type="unmatched_math_delimiters",
                    severity="warning",
                    message=f"数式記号が一致しません: {line.strip()}",
                    file_path=latex_file.path,
                    line_number=i,
                    suggestion="$ の数を確認してください"
                ))
            
            # 不正なコマンドチェック
            invalid_commands = re.findall(r'\\([a-zA-Z]+)', line)
            for cmd in invalid_commands:
                if cmd not in self.analyzer.standard_commands and cmd not in self.analyzer.global_commands:
                    # 一般的でないコマンドの場合は警告
                    if not self._is_common_package_command(cmd):
                        self.issues.append(ValidationIssue(
                            type="unknown_command",
                            severity="warning",
                            message=f"未知のコマンドです: \\{cmd}",
                            file_path=latex_file.path,
                            line_number=i,
                            suggestion="コマンドが正しいか、必要なパッケージが読み込まれているか確認してください"
                        ))

    def _validate_dependencies(self):
        """依存関係の検証"""
        for file_path, latex_file in self.analyzer.files.items():
            for dep in latex_file.dependencies:
                if dep not in self.analyzer.files:
                    self.issues.append(ValidationIssue(
                        type="missing_dependency",
                        severity="error",
                        message=f"依存ファイルが見つかりません: {dep}",
                        file_path=file_path,
                        suggestion=f"{dep} ファイルを作成するか、パスを確認してください"
                    ))

    def _validate_references(self):
        """参照の整合性検証"""
        reference_issues = self.analyzer.validate_references()
        
        for missing_label in reference_issues['missing_labels']:
            self.issues.append(ValidationIssue(
                type="missing_label",
                severity="error",
                message=f"参照先のラベルが見つかりません: {missing_label}",
                file_path=missing_label.split(':')[0],
                suggestion="対応するラベルを追加してください"
            ))

    def _validate_custom_definitions(self):
        """カスタムコマンド/環境の検証"""
        for file_path, latex_file in self.analyzer.files.items():
            # カスタムコマンドの使用チェック
            for cmd_name in latex_file.used_commands:
                if cmd_name in self.analyzer.global_commands:
                    cmd_def = self.analyzer.global_commands[cmd_name]
                    if cmd_def.source_file != file_path:
                        # 他のファイルで定義されているコマンドを使用している場合
                        if cmd_def.source_file not in latex_file.dependencies:
                            self.issues.append(ValidationIssue(
                                type="missing_command_dependency",
                                severity="warning",
                                message=f"コマンド \\{cmd_name} が {cmd_def.source_file} で定義されていますが、依存関係がありません",
                                file_path=file_path,
                                suggestion=f"\\input{{{cmd_def.source_file}}} を追加してください"
                            ))

    def _validate_latex_syntax(self):
        """LaTeX構文の検証"""
        for file_path, latex_file in self.analyzer.files.items():
            elements = self.parser.parse(latex_file.content)
            
            # 環境の対応チェック
            env_stack = []
            for element in elements:
                if element.type.name == 'ENVIRONMENT':
                    env_match = re.match(r'\\begin\{([^}]+)\}', element.content)
                    if env_match:
                        env_name = env_match.group(1)
                        env_stack.append(env_name)
                    
                    end_match = re.search(r'\\end\{([^}]+)\}', element.content)
                    if end_match:
                        end_env = end_match.group(1)
                        if env_stack and env_stack[-1] == end_env:
                            env_stack.pop()
                        else:
                            self.issues.append(ValidationIssue(
                                type="unmatched_environment",
                                severity="error",
                                message=f"環境が正しく閉じられていません: {end_env}",
                                file_path=file_path,
                                suggestion=f"\\begin{{{end_env}}} に対応する \\end{{{end_env}}} を確認してください"
                            ))
            
            # 未閉じの環境をチェック
            for env_name in env_stack:
                self.issues.append(ValidationIssue(
                    type="unclosed_environment",
                    severity="error",
                    message=f"環境が閉じられていません: {env_name}",
                    file_path=file_path,
                    suggestion=f"\\end{{{env_name}}} を追加してください"
                ))

    def _is_common_package_command(self, command: str) -> bool:
        """一般的なパッケージコマンドかどうかチェック"""
        common_package_commands = {
            # amsmath
            'align', 'gather', 'multline', 'split', 'aligned', 'gathered',
            'cases', 'matrix', 'pmatrix', 'bmatrix', 'vmatrix', 'Vmatrix',
            # amssymb
            'mathbb', 'mathfrak', 'mathscr',
            # graphicx
            'includegraphics', 'rotatebox', 'scalebox',
            # hyperref
            'href', 'url', 'hyperref', 'hypersetup',
            # geometry
            'geometry', 'newgeometry',
            # fancyhdr
            'fancyhf', 'fancyhead', 'fancyfoot', 'pagestyle',
            # babel
            'selectlanguage', 'foreignlanguage',
            # natbib
            'citep', 'citet', 'citealp', 'citealt', 'citeauthor', 'citeyear',
            # tikz
            'tikz', 'tikzpicture', 'node', 'draw', 'fill', 'path',
            # listings
            'lstlisting', 'lstinputlisting', 'lstset',
            # algorithm
            'algorithm', 'algorithmic', 'algsetup',
        }
        return command in common_package_commands

    def auto_fix_issues(self) -> Dict[str, str]:
        """自動修正可能な問題を修正"""
        fixed_files = {}
        
        for file_path, latex_file in self.analyzer.files.items():
            original_content = latex_file.content
            fixed_content = self._fix_file_content(original_content, file_path)
            
            if fixed_content != original_content:
                fixed_files[file_path] = fixed_content
                self.fixes_applied.append(f"Fixed issues in {file_path}")
        
        return fixed_files

    def _fix_file_content(self, content: str, file_path: str) -> str:
        """ファイル内容の自動修正"""
        # 全角文字を半角に修正
        full_to_half = {
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
        
        for full, half in full_to_half.items():
            content = content.replace(full, half)
        
        # 余分な空行を削除
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 数式内の不正な空白を修正
        content = re.sub(r'\$\s+([^$]+)\s+\$', r'$\1$', content)
        
        # コマンドと引数の間の不正な空白を修正
        content = re.sub(r'\\([a-zA-Z]+)\s+\{', r'\\\1{', content)
        
        return content

    def test_compilation(self, temp_dir: Optional[str] = None) -> Dict[str, Any]:
        """テストコンパイル実行"""
        if not self.analyzer.main_file:
            return {
                'success': False,
                'error': 'メインファイルが見つかりません',
                'output': '',
                'log': ''
            }
        
        try:
            with tempfile.TemporaryDirectory(dir=temp_dir) as tmp_dir:
                tmp_path = Path(tmp_dir)
                
                # ファイルをコピー
                for file_path, latex_file in self.analyzer.files.items():
                    target_file = tmp_path / file_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(latex_file.content)
                
                # LaTeX コンパイル実行
                main_file_path = tmp_path / self.analyzer.main_file
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', str(main_file_path)],
                    cwd=tmp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # ログファイルを読み込み
                log_file = main_file_path.with_suffix('.log')
                log_content = ""
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                
                return {
                    'success': result.returncode == 0,
                    'error': result.stderr if result.returncode != 0 else '',
                    'output': result.stdout,
                    'log': log_content,
                    'return_code': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'コンパイルがタイムアウトしました',
                'output': '',
                'log': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'コンパイルエラー: {str(e)}',
                'output': '',
                'log': ''
            }

    def get_compilation_safe_context(self, file_path: str) -> Dict[str, Any]:
        """コンパイル安全な翻訳コンテキストを取得"""
        context = self.analyzer.get_translation_context(file_path)
        
        # 検証結果を追加
        file_issues = [issue for issue in self.issues if issue.file_path == file_path]
        
        context.update({
            'validation_issues': [
                {
                    'type': issue.type,
                    'severity': issue.severity,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                }
                for issue in file_issues
            ],
            'critical_commands': self._get_critical_commands(file_path),
            'safe_translation_rules': self._get_safe_translation_rules(file_path),
        })
        
        return context

    def _get_critical_commands(self, file_path: str) -> List[str]:
        """翻訳時に特に注意すべきコマンドを取得"""
        if file_path not in self.analyzer.files:
            return []
        
        latex_file = self.analyzer.files[file_path]
        critical_commands = []
        
        # カスタムコマンドは特に注意
        for cmd in latex_file.used_commands:
            if cmd in self.analyzer.global_commands:
                critical_commands.append(cmd)
        
        return critical_commands

    def _get_safe_translation_rules(self, file_path: str) -> List[str]:
        """安全な翻訳のためのルール"""
        rules = [
            "LaTeXコマンドと環境は一切変更しない",
            "数式記号（$, \\(, \\), {, }, \\, &, %）は絶対に変更しない",
            "\\cite, \\ref, \\label内のキーは変更しない",
            "カスタムコマンドは翻訳しない",
            "ファイル名やパスは変更しない",
        ]
        
        # ファイル固有のルールを追加
        if file_path in self.analyzer.files:
            latex_file = self.analyzer.files[file_path]
            
            if latex_file.custom_commands:
                rules.append(f"カスタムコマンド（{', '.join([cmd.name for cmd in latex_file.custom_commands])}）は変更しない")
            
            if latex_file.custom_environments:
                rules.append(f"カスタム環境（{', '.join([env.name for env in latex_file.custom_environments])}）は変更しない")
        
        return rules