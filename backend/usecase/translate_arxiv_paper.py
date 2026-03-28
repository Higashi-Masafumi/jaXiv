import asyncio
import shutil
from collections.abc import AsyncGenerator
from logging import getLogger
from pathlib import Path

from domain.entities import (
	CompleteTranslateChunk,
	ErrorTranslateChunk,
	IntermediateTranslateChunk,
	LatexFile,
	TypedTranslateChunk,
)
from domain.errors import TexFileNotFoundError
from domain.gateways import (
	IArxivSourceFetcher,
	ILatexCompiler,
	ILatexTranslator,
)
from domain.value_objects import ArxivPaperId, TargetLanguage


class TranslateArxivPaper:
	"""Use case for translating an arXiv paper."""

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

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
		target_language: TargetLanguage,
		output_dir: str,
		max_workers: int = 5,
	) -> AsyncGenerator[TypedTranslateChunk]:
		"""
		Translate an arXiv paper and yield progress chunks.

		Args:
		    arxiv_paper_id: The ID of the paper to translate.
		    target_language: The language to translate to.
		    output_dir: The directory to save the translated paper to.
		    max_workers: Maximum concurrent translation workers.

		Yields:
		    TypedTranslateChunk with translation progress.
		"""
		self._logger.info('Translating %s to %s', arxiv_paper_id.root, target_language)
		yield IntermediateTranslateChunk(
			message=f'Translating Arxiv {arxiv_paper_id.root} to {target_language}',
			progress_percentage=0,
		)

		# 1. Fetch tex source
		compile_setting = self._arxiv_source_fetcher.fetch_tex_source(
			paper_id=arxiv_paper_id, output_dir=output_dir
		)
		yield IntermediateTranslateChunk(
			message=f'Fetched tex source for Arxiv {arxiv_paper_id.root}',
			progress_percentage=10,
		)

		# 2. List tex files
		tex_file_paths = list(Path(compile_setting.source_directory).rglob('*.tex'))
		if len(tex_file_paths) == 0:
			yield ErrorTranslateChunk(
				message=f'No tex file found in the source directory for Arxiv {arxiv_paper_id.root}',
				progress_percentage=10,
				error_details='チェックポイント: texファイルが存在しない、または拡張子が異なる可能性があります。',
			)
			raise TexFileNotFoundError(compile_setting.source_directory)

		self._logger.info('Found %d tex files in the source directory', len(tex_file_paths))
		latex_files: list[LatexFile] = [
			LatexFile(path=str(p), content=p.read_text()) for p in tex_file_paths
		]

		# 3. Translate in parallel
		yield IntermediateTranslateChunk(
			message=f'Starting translation of tex files for Arxiv {arxiv_paper_id.root}',
			progress_percentage=20,
		)

		translated_latex_files: list[LatexFile] = []
		progress_by_file = 50 / len(latex_files) if len(latex_files) > 0 else 0
		semaphore = asyncio.Semaphore(max_workers)

		async def translate_latex_file(latex_file: LatexFile) -> LatexFile:
			async with semaphore:
				return await self._latex_translator.translate(
					latex_file=latex_file, target_language=target_language
				)

		tasks = [asyncio.create_task(translate_latex_file(lf)) for lf in latex_files]
		for i, task in enumerate(asyncio.as_completed(tasks)):
			translated_file = await task
			translated_latex_files.append(translated_file)
			yield IntermediateTranslateChunk(
				message=f'Translated {i + 1}/{len(latex_files)} tex files for Arxiv {arxiv_paper_id.root}',
				progress_percentage=round(20 + progress_by_file * (i + 1)),
			)

		# 4. Write translated content to files
		for translated_file in translated_latex_files:
			with open(translated_file.path, 'w') as f:
				f.write(translated_file.content)

		# 5. Compile
		yield IntermediateTranslateChunk(
			message=f'Compiling translated tex files for Arxiv {arxiv_paper_id.root}',
			progress_percentage=70,
		)
		try:
			compiled_pdf_path = self._latex_compiler.compile(compile_setting=compile_setting)
			yield CompleteTranslateChunk(
				message=f'Compiled translated tex files for Arxiv {arxiv_paper_id.root}',
				progress_percentage=90,
				translated_pdf_path=compiled_pdf_path,
			)
		except Exception as e:
			self._logger.error('Error compiling %s: %s', arxiv_paper_id.root, e)
			yield ErrorTranslateChunk(
				message=f'Error compiling translated tex files for Arxiv {arxiv_paper_id.root}',
				progress_percentage=70,
				error_details=str(e),
			)
			shutil.rmtree(compile_setting.source_directory)
			raise
