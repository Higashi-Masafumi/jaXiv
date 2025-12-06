import asyncio
import shutil
from collections.abc import AsyncGenerator
from logging import getLogger
from pathlib import Path

from domain.entities import (
    ArxivPaperId,
    CompleteTranslateChunk,
    ErrorTranslateChunk,
    IntermediateTranslateChunk,
    LatexFile,
    TargetLanguage,
    TypedTranslateChunk,
)
from domain.repositories import (
    IArxivSourceFetcher,
    ILatexCompiler,
    ILatexTranslator,
)


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
        max_workers: int = 5,
    ) -> AsyncGenerator[TypedTranslateChunk]:
        """
        Translate an arxiv paper.

        Args:
            arxiv_paper_id (ArxivPaperId): The ID of the paper to translate.
            target_language (TargetLanguage): The language to translate the paper to.
            output_dir (str): The directory to save the translated paper to.
            event_streamer (IEventStreamer): The event streamer to stream events to.

        Raises:
            FileNotFoundError: If no tex file is found in the source directory.

        Returns:
            str: The path to the compiled pdf file.

        Example:
            >>> translate_arxiv_paper = TranslateArxivPaper(
            >>>     arxiv_source_fetcher=arxiv_source_fetcher,
            >>>     latex_compiler=latex_compiler,
            >>>     latex_translator=latex_translator,
            >>> )
            >>> translate_arxiv_paper.translate(arxiv_paper_id=ArxivPaperId(root="1234.5678"), target_language=TargetLanguage.EN, output_dir="output")
        """
        self._logger.info(f"Translating {arxiv_paper_id} to {target_language}")
        yield IntermediateTranslateChunk(
            message=f"Translating Arxiv {arxiv_paper_id} to {target_language}",
            progress_percentage=0,
        )
        # 1. 論文のtexファイルを取得
        compile_setting = self._arxiv_source_fetcher.fetch_tex_source(
            paper_id=arxiv_paper_id, output_dir=output_dir
        )
        # 進捗をストリーミング
        yield IntermediateTranslateChunk(
            message=f"Fetched tex source for Arxiv {arxiv_paper_id}",
            progress_percentage=10,
        )

        # 2. ソースフォルダ内でtex fileをリストアップする
        # 再帰的に*.texファイルを検索する
        tex_file_paths = list(Path(compile_setting.source_directory).rglob("*.tex"))
        if len(tex_file_paths) == 0:
            # エラーをストリーミング
            yield ErrorTranslateChunk(
                message=f"No tex file found in the source directory for Arxiv {arxiv_paper_id}",
                progress_percentage=10,
                error_details="チェックポイント: texファイルが存在しない、または拡張子が異なる可能性があります。",
            )
            raise FileNotFoundError("No tex file found in the source directory")
        else:
            self._logger.info(
                f"Found {len(tex_file_paths)} tex files in the source directory"
            )
            latex_files: list[LatexFile] = []
            for tex_file_path in tex_file_paths:
                latex_file = LatexFile(
                    path=str(tex_file_path),
                    content=tex_file_path.read_text(),
                )
                latex_files.append(latex_file)

        # 3. 翻訳
        # 進捗をストリーミング
        yield IntermediateTranslateChunk(
            message=f"Starting translation of tex files for Arxiv {arxiv_paper_id}",
            progress_percentage=20,
        )

        # 翻訳は並列化する
        translated_latex_files: list[LatexFile] = []
        progress_by_file = 50 / len(latex_files) if len(latex_files) > 0 else 0
        semaphore = asyncio.Semaphore(max_workers)

        async def translate_latex_file(latex_file: LatexFile) -> LatexFile:
            async with semaphore:
                translated_latex_file = await self._latex_translator.translate(
                    latex_file=latex_file, target_language=target_language
                )
                return translated_latex_file

        tasks = [
            asyncio.create_task(translate_latex_file(latex_file))
            for latex_file in latex_files
        ]
        self._logger.info(f"Translated {len(translated_latex_files)} tex files")

        for i, task in enumerate(asyncio.as_completed(tasks)):
            translated_latex_file = await task
            translated_latex_files.append(translated_latex_file)
            # 進捗をストリーミング
            yield IntermediateTranslateChunk(
                message=f"Translated {i + 1}/{len(latex_files)} tex files for Arxiv {arxiv_paper_id}",
                progress_percentage=round(20 + progress_by_file * (i + 1)),
            )

        # 4. 翻訳後のtex contentをtex fileに書き込む
        for translated_latex_file in translated_latex_files:
            with open(translated_latex_file.path, "w") as f:
                f.write(translated_latex_file.content)

        # 5. 翻訳後のtex fileをコンパイル
        # 進捗をストリーミング
        yield IntermediateTranslateChunk(
            message=f"Compiling translated tex files for Arxiv {arxiv_paper_id}",
            progress_percentage=70,
        )
        # コンパイルは失敗する可能性があるので、try-exceptで囲う
        try:
            compiled_pdf_file_path = self._latex_compiler.compile(
                compile_setting=compile_setting
            )
            # 進捗をストリーミング
            yield CompleteTranslateChunk(
                message=f"Compiled translated tex files for Arxiv {arxiv_paper_id}",
                progress_percentage=90,
                translated_pdf_path=compiled_pdf_file_path,
            )
        except Exception as e:
            self._logger.error(f"Error compiling {arxiv_paper_id}: {e}")
            yield ErrorTranslateChunk(
                message=f"Error compiling translated tex files for Arxiv {arxiv_paper_id}",
                progress_percentage=70,
                error_details=str(e),
            )
            shutil.rmtree(compile_setting.source_directory)
            raise e
