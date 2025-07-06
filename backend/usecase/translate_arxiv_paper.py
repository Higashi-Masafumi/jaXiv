from domain.repositories import IArxivSourceFetcher, ILatexCompiler, ILatexTranslator
from domain.entities import CompileSetting, ArxivPaperId, LatexFile, TargetLanguage
from logging import getLogger
import os
from pathlib import Path


class TranslateArxivPaper:
    """
    Translate an arxiv paper.
    """

    def __init__(
        self,
        arxiv_source_fetcher: IArxivSourceFetcher,
        latex_compiler: ILatexCompiler,
        latex_translator: ILatexTranslator,
    ):
        self._logger = getLogger(__name__)
        self._arxiv_source_fetcher = arxiv_source_fetcher
        self._latex_compiler = latex_compiler
        self._latex_translator = latex_translator

    async def translate(
        self,
        arxiv_paper_id: ArxivPaperId,
        target_language: TargetLanguage,
        output_dir: str,
    ) -> str:
        self._logger.info(f"Translating {arxiv_paper_id} to {target_language}")
        # 1. 論文のtexファイルを取得
        compile_setting = self._arxiv_source_fetcher.fetch_tex_source(
            paper_id=arxiv_paper_id, output_dir=output_dir
        )
        # 2. ソースフォルダ内でtex fileをリストアップする
        # 再帰的に*.texファイルを検索する
        tex_file_paths = list(Path(compile_setting.source_directory).rglob("*.tex"))
        if len(tex_file_paths) == 0:
            raise FileNotFoundError("No tex file found in the source directory")
        else:
            self._logger.info(f"Found {len(tex_file_paths)} tex files in the source directory")
            latex_files: list[LatexFile] = []
            for tex_file_path in tex_file_paths:
                latex_file = LatexFile(
                    path=str(tex_file_path),
                    content=tex_file_path.read_text(),
                )
                latex_files.append(latex_file)
        # 3. 翻訳
        translated_latex_files: list[LatexFile] = []
        for latex_file in latex_files:
            translated_latex_file = await self._latex_translator.translate(
                latex_file=latex_file, target_language=target_language
            )
            translated_latex_files.append(translated_latex_file)
            self._logger.info(f"Translated {latex_file.path}")
        # 4. 翻訳後のtex contentをtex fileに書き込む
        for translated_latex_file in translated_latex_files:
            with open(translated_latex_file.path, "w") as f:
                f.write(translated_latex_file.content)
        # 5. 翻訳後のtex fileをコンパイル
        compiled_pdf_file_path = self._latex_compiler.compile(
            compile_setting=compile_setting
        )
        # 6. 翻訳後のpdf fileを保存
        return compiled_pdf_file_path
