from logging import getLogger

from domain.entities import ArxivPaperMetadataWithTranslatedUrl
from domain.repositories import ITranslatedArxivRepository
from domain.value_objects import ArxivPaperId


class ArxivRedirecter:
	"""Use case for checking if a translated paper already exists."""

	def __init__(self, translated_arxiv_repository: ITranslatedArxivRepository):
		self._translated_arxiv_repository = translated_arxiv_repository
		self._logger = getLogger(__name__)

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
	) -> ArxivPaperMetadataWithTranslatedUrl | None:
		"""
		Check if a translated version of the paper exists.

		Args:
		    arxiv_paper_id: The arXiv paper ID to check.

		Returns:
		    The translated metadata if found, None otherwise.
		"""
		translated_paper_metadata = await self._translated_arxiv_repository.find_by_paper_id(
			arxiv_paper_id
		)
		if translated_paper_metadata is None:
			self._logger.info(
				'Translated paper metadata not found for %s',
				arxiv_paper_id.value,
			)
			return None
		return translated_paper_metadata
