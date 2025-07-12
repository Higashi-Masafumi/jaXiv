from typing import Dict, List, Any, Optional
from logging import getLogger
from pathlib import Path
import tempfile
import shutil

from domain.entities import LatexFile, TargetLanguage, TranslatedLatexFile, CompileSetting
from domain.repositories import ILatexTranslator, ILatexCompiler, IFileStorageRepository
from utils import LatexProjectAnalyzer, LatexValidator
from utils.latex_translator_base import BaseLatexTranslator


class TranslateLatexProjectUseCase:
    """LaTeXプロジェクト全体の翻訳を管理するユースケース"""
    
    def __init__(
        self,
        latex_translator: ILatexTranslator,
        latex_compiler: ILatexCompiler,
        storage_repository: IFileStorageRepository,
    ):
        self._translator = latex_translator
        self._compiler = latex_compiler
        self._storage = storage_repository
        self._logger = getLogger(__name__)

    async def translate_project(
        self,
        project_path: str,
        target_language: TargetLanguage,
        output_path: Optional[str] = None,
        validate_compilation: bool = True,
    ) -> Dict[str, Any]:
        """プロジェクト全体を翻訳"""
        
        self._logger.info(f"Starting project translation: {project_path}")
        
        # 1. プロジェクト解析
        analyzer = LatexProjectAnalyzer(project_path)
        analysis_result = analyzer.analyze_project()
        
        self._logger.info(f"Project analysis completed: {analysis_result['project_structure']}")
        
        # 2. 翻訳前の検証
        validator = LatexValidator(analyzer)
        validation_result = validator.validate_project()
        
        if validation_result['error_count'] > 0:
            self._logger.warning(f"Project has {validation_result['error_count']} validation errors")
            
            # 自動修正を試行
            auto_fixes = validator.auto_fix_issues()
            if auto_fixes:
                self._logger.info(f"Applied auto-fixes to {len(auto_fixes)} files")
                for file_path, fixed_content in auto_fixes.items():
                    analyzer.files[file_path].content = fixed_content
        
        # 3. 翻訳器にプロジェクトコンテキストを設定
        if isinstance(self._translator, BaseLatexTranslator):
            self._translator.set_project_context(project_path)
        
        # 4. 翻訳実行
        translated_files = {}
        translation_errors = []
        
        # コンパイル順序で翻訳
        for file_path in analysis_result['compilation_order']:
            if file_path in analyzer.files:
                try:
                    analyzer_file = analyzer.files[file_path]
                    # Domain entityに変換
                    latex_file = LatexFile(
                        path=analyzer_file.path,
                        content=analyzer_file.content
                    )
                    self._logger.info(f"Translating {file_path}")
                    
                    translated_file = await self._translator.translate(
                        latex_file, target_language
                    )
                    translated_files[file_path] = translated_file
                    
                except Exception as e:
                    error_msg = f"Failed to translate {file_path}: {str(e)}"
                    self._logger.error(error_msg)
                    translation_errors.append(error_msg)
                    # 翻訳失敗時は元のファイルを保持
                    translated_files[file_path] = analyzer.files[file_path]
        
        # 5. 翻訳後の検証
        post_translation_validation = None
        if validate_compilation:
            post_translation_validation = await self._validate_translated_project(
                translated_files, analysis_result['main_file']
            )
        
        # 6. 出力ファイルの準備
        output_files = []
        if output_path:
            output_files = await self._save_translated_project(
                translated_files, output_path, project_path
            )
        
        # 7. 結果の準備
        result = {
            'success': len(translation_errors) == 0,
            'analysis_result': analysis_result,
            'validation_result': validation_result,
            'post_translation_validation': post_translation_validation,
            'translated_files': list(translated_files.keys()),
            'translation_errors': translation_errors,
            'output_files': output_files,
            'statistics': {
                'total_files': len(analyzer.files),
                'translated_files': len(translated_files),
                'failed_files': len(translation_errors),
                'custom_commands': len(analysis_result['global_commands']),
                'custom_environments': len(analysis_result['global_environments']),
            }
        }
        
        self._logger.info(f"Project translation completed: {result['statistics']}")
        return result

    async def _validate_translated_project(
        self,
        translated_files: Dict[str, LatexFile],
        main_file: str
    ) -> Dict[str, Any]:
        """翻訳後のプロジェクトをコンパイルして検証"""
        
        self._logger.info("Validating translated project compilation")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 翻訳されたファイルを一時ディレクトリにコピー
                for file_path, latex_file in translated_files.items():
                    target_file = temp_path / file_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(latex_file.content)
                
                # コンパイルテスト
                if main_file:
                    compile_setting = CompileSetting(
                        target_file_name=main_file,
                        source_directory=str(temp_path),
                        engine="pdflatex",
                        use_bibtex=True
                    )
                    
                    try:
                        output_path = self._compiler.compile(compile_setting)
                        return {
                            'compilation_successful': True,
                            'error_message': None,
                            'warnings': [],
                            'output_files': [output_path] if output_path else [],
                        }
                    except Exception as e:
                        return {
                            'compilation_successful': False,
                            'error_message': str(e),
                            'warnings': [],
                            'output_files': [],
                        }
                else:
                    return {
                        'compilation_successful': False,
                        'error_message': 'No main file found',
                        'warnings': [],
                        'output_files': [],
                    }
                    
        except Exception as e:
            self._logger.error(f"Compilation validation failed: {str(e)}")
            return {
                'compilation_successful': False,
                'error_message': str(e),
                'warnings': [],
                'output_files': [],
            }

    async def _save_translated_project(
        self,
        translated_files: Dict[str, LatexFile],
        output_path: str,
        original_project_path: str
    ) -> List[str]:
        """翻訳されたプロジェクトを保存"""
        
        self._logger.info(f"Saving translated project to {output_path}")
        
        output_files = []
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 元のプロジェクトの非LaTeXファイルをコピー
            original_path = Path(original_project_path)
            for item in original_path.rglob('*'):
                if item.is_file() and not item.suffix.lower() in ['.tex', '.latex']:
                    relative_path = item.relative_to(original_path)
                    target_path = output_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
                    output_files.append(str(relative_path))
            
            # 翻訳されたファイルを保存
            for file_path, latex_file in translated_files.items():
                target_file = output_dir / file_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(latex_file.content)
                    
                output_files.append(file_path)
                
                self._logger.debug(f"Saved {file_path} to output directory")
            
            return output_files
            
        except Exception as e:
            self._logger.error(f"Failed to save translated project: {str(e)}")
            raise

    async def get_project_summary(self, project_path: str) -> Dict[str, Any]:
        """プロジェクトの概要情報を取得"""
        
        analyzer = LatexProjectAnalyzer(project_path)
        analysis_result = analyzer.analyze_project()
        
        validator = LatexValidator(analyzer)
        validation_result = validator.validate_project()
        
        # 翻訳見積もり
        total_text_length = 0
        translatable_elements = 0
        
        for latex_file in analyzer.files.values():
            elements = analyzer.parser.parse(latex_file.content)
            for element in elements:
                if element.should_translate and element.type.name == 'TEXT':
                    total_text_length += len(element.content)
                    translatable_elements += 1
        
        return {
            'project_structure': analysis_result['project_structure'],
            'validation_summary': {
                'is_compilable': validation_result['is_compilable'],
                'error_count': validation_result['error_count'],
                'warning_count': validation_result['warning_count'],
            },
            'translation_estimate': {
                'total_files': len(analyzer.files),
                'translatable_elements': translatable_elements,
                'estimated_text_length': total_text_length,
                'estimated_tokens': total_text_length // 4,  # 概算
            },
            'custom_definitions': {
                'commands': list(analysis_result['global_commands'].keys()),
                'environments': list(analysis_result['global_environments'].keys()),
            },
            'dependencies': analysis_result['dependency_graph'],
        }

    async def validate_project_before_translation(self, project_path: str) -> Dict[str, Any]:
        """翻訳前のプロジェクト検証"""
        
        analyzer = LatexProjectAnalyzer(project_path)
        analysis_result = analyzer.analyze_project()
        
        validator = LatexValidator(analyzer)
        validation_result = validator.validate_project()
        
        # コンパイルテスト
        compilation_result = None
        if validation_result['is_compilable']:
            compilation_result = validator.test_compilation()
        
        return {
            'analysis_result': analysis_result,
            'validation_result': validation_result,
            'compilation_result': compilation_result,
            'recommendations': self._get_translation_recommendations(
                analysis_result, validation_result
            ),
        }

    def _get_translation_recommendations(
        self,
        analysis_result: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> List[str]:
        """翻訳のための推奨事項を生成"""
        
        recommendations = []
        
        # エラーがある場合
        if validation_result['error_count'] > 0:
            recommendations.append(
                f"翻訳前に{validation_result['error_count']}個のエラーを修正することを推奨します"
            )
        
        # 警告がある場合
        if validation_result['warning_count'] > 0:
            recommendations.append(
                f"{validation_result['warning_count']}個の警告があります。翻訳品質に影響する可能性があります"
            )
        
        # カスタム定義が多い場合
        custom_count = len(analysis_result['global_commands']) + len(analysis_result['global_environments'])
        if custom_count > 10:
            recommendations.append(
                f"カスタムコマンド/環境が{custom_count}個あります。翻訳時に特に注意が必要です"
            )
        
        # 複雑な依存関係がある場合
        max_deps = max(len(deps) for deps in analysis_result['dependency_graph'].values()) if analysis_result['dependency_graph'] else 0
        if max_deps > 5:
            recommendations.append(
                "複雑な依存関係があります。翻訳順序に注意してください"
            )
        
        return recommendations