from logging import getLogger

from pydantic import HttpUrl

from domain.entities import ArxivPaperMetadataWithTranslatedUrl
from domain.gateways import IArxivSourceFetcher
from domain.repositories import (
	IFileStorageRepository,
	ITranslatedArxivRepository,
)
from domain.value_objects import ArxivPaperId


class SaveTranslatedArxivUseCase:
	"""Upload translated PDF bytes to storage and persist the metadata."""

	def __init__(
		self,
		translated_arxiv_repository: ITranslatedArxivRepository,
		file_storage_repository: IFileStorageRepository,
		arxiv_source_fetcher: IArxivSourceFetcher,
	):
		self._logger = getLogger(__name__)
		self._translated_arxiv_repository = translated_arxiv_repository
		self._file_storage_repository = file_storage_repository
		self._arxiv_source_fetcher = arxiv_source_fetcher

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
		translated_pdf_bytes: bytes,
	) -> ArxivPaperMetadataWithTranslatedUrl:
		self._logger.info('Saving translated arxiv paper %s', arxiv_paper_id.root)

		arxiv_paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
			paper_id=arxiv_paper_id
		)

		storage_path = f'{arxiv_paper_id.root}_translated.pdf'
		translated_pdf_url = await self._file_storage_repository.save_translated_file_and_get_url(
			storage_path=storage_path,
			content=translated_pdf_bytes,
		)

		metadata_with_url = arxiv_paper_metadata.with_translated_url(
			translated_file_storage_path=storage_path,
			translated_url=HttpUrl(translated_pdf_url),
		)

		await self._translated_arxiv_repository.save(translated_paper_metadata=metadata_with_url)

		return metadata_with_url
