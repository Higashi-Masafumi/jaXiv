import asyncio
from logging import getLogger
from pathlib import Path

from domain.entities import LatexFile
from domain.errors import TexFileNotFoundError
from domain.gateways import IArxivSourceFetcher, ILatexCompiler, ILatexTranslator
from domain.value_objects import ArxivPaperId, TargetLanguage


class TranslateArxivPaperUseCase:
    """Fetch, translate and compile an arXiv paper into a PDF on disk."""

    def __init__(
        self,
        arxiv_source_fetcher: IArxivSourceFetcher,
        latex_compiler: ILatexCompiler,
        latex_translator: ILatexTranslator,
    ) -> None:
        self._logger = getLogger(__name__)
        self._arxiv_source_fetcher = arxiv_source_fetcher
        self._latex_compiler = latex_compiler
        self._latex_translator = latex_translator

    async def execute(
        self,
        arxiv_paper_id: ArxivPaperId,
        target_language: TargetLanguage,
        output_dir: str,
        max_workers: int = 5,
    ) -> str:
        self._logger.info(
            "Translating %s to %s", arxiv_paper_id.root, target_language
        )

        compile_setting = self._arxiv_source_fetcher.fetch_tex_source(
            paper_id=arxiv_paper_id, output_dir=output_dir
        )

        tex_file_paths = list(
            Path(compile_setting.source_directory).rglob("*.tex")
        )
        if len(tex_file_paths) == 0:
            raise TexFileNotFoundError(compile_setting.source_directory)
        self._logger.info(
            "Found %d tex files in the source directory", len(tex_file_paths)
        )

        latex_files: list[LatexFile] = [
            LatexFile(path=str(p), content=p.read_text()) for p in tex_file_paths
        ]

        semaphore = asyncio.Semaphore(max_workers)

        async def translate_one(latex_file: LatexFile) -> LatexFile:
            async with semaphore:
                return await self._latex_translator.translate(
                    latex_file=latex_file, target_language=target_language
                )

        translated_latex_files = await asyncio.gather(
            *[translate_one(lf) for lf in latex_files]
        )

        for translated_file in translated_latex_files:
            with open(translated_file.path, "w") as f:
                f.write(translated_file.content)

        return self._latex_compiler.compile(compile_setting=compile_setting)
