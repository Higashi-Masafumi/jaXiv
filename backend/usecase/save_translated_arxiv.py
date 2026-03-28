import shutil
from logging import getLogger
from pathlib import Path

from pydantic import HttpUrl

from domain.entities import (
	ArxivPaperMetadataWithTranslatedUrl,
	TranslatedLatexFile,
)
from domain.gateways import IArxivSourceFetcher
from domain.repositories import (
	IFileStorageRepository,
	ITranslatedArxivRepository,
)
from domain.value_objects import ArxivPaperId


class SaveTranslatedArxivUseCase:
	"""Use case for saving a translated arXiv paper to storage and database."""

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
		translated_arxiv_pdf_path: str,
	) -> ArxivPaperMetadataWithTranslatedUrl:
		"""
		Save a translated arXiv paper.

		Args:
		    arxiv_paper_id: The arXiv paper ID.
		    translated_arxiv_pdf_path: Local path to the translated PDF.

		Returns:
		    Metadata with the translated URL.
		"""
		self._logger.info('Saving translated arxiv paper %s', arxiv_paper_id.value)

		# 1. Fetch paper metadata
		arxiv_paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
			paper_id=arxiv_paper_id
		)

		# 2. Upload translated PDF
		translated_file = TranslatedLatexFile(
			path=translated_arxiv_pdf_path,
			storage_path=f'{arxiv_paper_id.value}_translated.pdf',
		)
		translated_pdf_url = await self._file_storage_repository.save_translated_file_and_get_url(
			translated_file=translated_file
		)

		# 3. Clean up local files
		shutil.rmtree(Path(translated_arxiv_pdf_path).parent)

		# 4. Create metadata with translated URL
		metadata_with_url = arxiv_paper_metadata.with_translated_url(
			translated_file_storage_path=translated_file.storage_path,
			translated_url=HttpUrl(translated_pdf_url),
		)

		# 5. Persist metadata
		await self._translated_arxiv_repository.save(translated_paper_metadata=metadata_with_url)

		return metadata_with_url
