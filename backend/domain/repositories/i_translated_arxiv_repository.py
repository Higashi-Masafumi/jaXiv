from abc import ABC, abstractmethod

from domain.entities.arxiv import ArxivPaperId, ArxivPaperMetadataWithTranslatedUrl


class ITranslatedArxivRepository(ABC):
	"""
	A repository for fetching the translated metadata of a paper from arXiv.
	"""

	@abstractmethod
	def get_translated_paper_metadata(
		self, paper_id: ArxivPaperId
	) -> ArxivPaperMetadataWithTranslatedUrl | None:
		"""
		Fetch the translated metadata of a paper from arXiv.

		Args:
		    paper_id (ArxivPaperId): The ID of the paper to fetch the translated metadata for.

		Returns:
		    ArxivPaperMetadataWithTranslatedUrl: The translated metadata of the paper.

		>>> fetch_translated_paper_metadata(ArxivPaperId('1234.5678'))
		ArxivPaperMetadataWithTranslatedUrl(
		    paper_id=ArxivPaperId("1234.5678"),
		    title="The title of the paper",
		    summary="The summary of the paper",
		    published_date=PastDate(2021, 1, 1),
		)
		>>> fetch_translated_paper_metadata(ArxivPaperId('1234.5678')) is None
		True
		"""
		pass

	@abstractmethod
	def save_translated_paper_metadata(
		self, translated_paper_metadata: ArxivPaperMetadataWithTranslatedUrl
	) -> None:
		"""
		Save the translated metadata of a paper to the database.

		Args:
		    translated_paper_metadata (ArxivPaperMetadataWithTranslatedUrl): The translated metadata of the paper to save.

		Returns:
		    None
		"""
		pass
