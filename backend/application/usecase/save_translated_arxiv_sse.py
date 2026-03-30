import shutil
from logging import getLogger
from pathlib import Path

from pydantic import HttpUrl

from application.unit_of_works import TranslatedArxivUnitOfWork
from domain.entities import (
	ArxivPaperMetadataWithTranslatedUrl,
	TranslatedLatexFile,
)
from domain.gateways import IArxivSourceFetcher
from domain.repositories import IFileStorageRepository
from domain.value_objects import ArxivPaperId


class SaveTranslatedArxivSSEUseCase:
	"""Use case for saving a translated arXiv paper within an SSE-safe UoW."""

	def __init__(
		self,
		translated_arxiv_unit_of_work: TranslatedArxivUnitOfWork,
		file_storage_repository: IFileStorageRepository,
		arxiv_source_fetcher: IArxivSourceFetcher,
	):
		self._logger = getLogger(__name__)
		self._uow = translated_arxiv_unit_of_work
		self._file_storage_repository = file_storage_repository
		self._arxiv_source_fetcher = arxiv_source_fetcher

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
		translated_arxiv_pdf_path: str,
	) -> ArxivPaperMetadataWithTranslatedUrl:
		self._logger.info('Saving translated arxiv paper %s', arxiv_paper_id.root)

		arxiv_paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
			paper_id=arxiv_paper_id
		)

		translated_file = TranslatedLatexFile(
			path=translated_arxiv_pdf_path,
			storage_path=f'{arxiv_paper_id.root}_translated.pdf',
		)
		translated_pdf_url = await self._file_storage_repository.save_translated_file_and_get_url(
			translated_file=translated_file
		)

		shutil.rmtree(Path(translated_arxiv_pdf_path).parent)

		metadata_with_url = arxiv_paper_metadata.with_translated_url(
			translated_file_storage_path=translated_file.storage_path,
			translated_url=HttpUrl(translated_pdf_url),
		)

		async with self._uow as uow:
			await uow.translated_arxiv_repository.save(translated_paper_metadata=metadata_with_url)

		return metadata_with_url
