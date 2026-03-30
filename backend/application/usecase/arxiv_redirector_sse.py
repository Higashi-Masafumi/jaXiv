from logging import getLogger

from application.unit_of_works import TranslatedArxivUnitOfWork
from domain.entities import ArxivPaperMetadataWithTranslatedUrl
from domain.value_objects import ArxivPaperId


class ArxivRedirectorSSEUseCase:
	"""Use case for checking if a translated paper already exists within an SSE-safe UoW."""

	def __init__(self, translated_arxiv_unit_of_work: TranslatedArxivUnitOfWork):
		self._uow = translated_arxiv_unit_of_work
		self._logger = getLogger(__name__)

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
	) -> ArxivPaperMetadataWithTranslatedUrl | None:
		async with self._uow as uow:
			translated_paper_metadata = await uow.translated_arxiv_repository.find_by_paper_id(
				arxiv_paper_id
			)
		if translated_paper_metadata is None:
			self._logger.info(
				'Translated paper metadata not found for %s',
				arxiv_paper_id.root,
			)
			return None
		return translated_paper_metadata
