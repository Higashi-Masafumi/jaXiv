from domain.repositories import (
    IArxivSourceFetcher,
    ILatexCompiler,
    ILatexTranslator,
    IEventStreamer,
)
from domain.entities import ArxivPaperId, LatexFile, TargetLanguage
from logging import getLogger
import shutil
from pathlib import Path
import asyncio


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
        event_streamer: IEventStreamer,
        max_workers: int = 5,
    ) -> str:
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
        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id} のtexソースコードの取得を開始します。",
            arxiv_paper_id=arxiv_paper_id.root,
            progress_percentage=0,
        )
        # 1. 論文のtexファイルを取得
        compile_setting = self._arxiv_source_fetcher.fetch_tex_source(
            paper_id=arxiv_paper_id, output_dir=output_dir
        )
        # 進捗をストリーミング
        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id} のtexソースコードの取得を完了しました。",
            arxiv_paper_id=arxiv_paper_id.root,
            progress_percentage=10,
        )

        # 2. ソースフォルダ内でtex fileをリストアップする
        # 再帰的に*.texファイルを検索する
        tex_file_paths = list(Path(compile_setting.source_directory).rglob("*.tex"))
        if len(tex_file_paths) == 0:
            # エラーをストリーミング
            await event_streamer.stream_event(
                event_type="failed",
                message=f"Arxiv {arxiv_paper_id} のtexソース内にコンパイル対象となるtexファイルが見つかりませんでした。",
                arxiv_paper_id=arxiv_paper_id.root,
                progress_percentage=10,
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
        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id} のtexソース内にコンパイル対象となるtexファイルが{len(tex_file_paths)}個見つかりました。翻訳を開始します。",
            arxiv_paper_id=arxiv_paper_id.root,
            progress_percentage=20,
        )

        # 翻訳は並列化する
        translated_latex_files: list[LatexFile] = []
        tasks = []
        progress_by_file = 50 / len(latex_files) if len(latex_files) > 0 else 0
        semaphore = asyncio.Semaphore(max_workers)
        async def translate_latex_file(latex_file: LatexFile):
            async with semaphore:
                translated_latex_file = await self._latex_translator.translate(
                    latex_file=latex_file, target_language=target_language
                )
                translated_latex_files.append(translated_latex_file)
                await event_streamer.stream_event(
                    event_type="progress",
                    message=f"Arxiv {arxiv_paper_id.root} の{latex_file.path}の翻訳を完了しました。（{len(translated_latex_files)}/{len(latex_files)}個目）",
                    arxiv_paper_id=arxiv_paper_id.root,
                    progress_percentage=20 + progress_by_file * len(translated_latex_files),
                )
        tasks = [translate_latex_file(latex_file) for latex_file in latex_files]
        await asyncio.gather(*tasks)
        self._logger.info(f"Translated {len(translated_latex_files)} tex files")

        # 4. 翻訳後のtex contentをtex fileに書き込む
        for translated_latex_file in translated_latex_files:
            with open(translated_latex_file.path, "w") as f:
                f.write(translated_latex_file.content)

        # 5. 翻訳後のtex fileをコンパイル
        # 進捗をストリーミング
        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id} のtexソース内のtexファイルの翻訳を完了しました。コンパイルを開始します",
            arxiv_paper_id=arxiv_paper_id.root,
            progress_percentage=70,
        )
        # コンパイルは失敗する可能性があるので、try-exceptで囲う
        try:
            compiled_pdf_file_path = self._latex_compiler.compile(
                compile_setting=compile_setting
            )
            # 進捗をストリーミング
            await event_streamer.stream_event(
                event_type="progress",
                message=f"Arxiv {arxiv_paper_id} のtexソース内のtexファイルのコンパイルを完了しました。",
                arxiv_paper_id=arxiv_paper_id.root,
                progress_percentage=80,
            )
        except Exception as e:
            self._logger.error(f"Error compiling {arxiv_paper_id}: {e}")
            await event_streamer.stream_event(
                event_type="failed",
                message=f"Arxiv {arxiv_paper_id} のtexソース内のtexファイルのコンパイルに失敗しました。",
                arxiv_paper_id=arxiv_paper_id.root,
                progress_percentage=80,
            )
            await event_streamer.finish()
            shutil.rmtree(compile_setting.source_directory)
            raise e
        # 6. 翻訳後のpdf fileを保存
        return compiled_pdf_file_path
