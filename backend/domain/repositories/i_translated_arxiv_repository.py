from abc import ABC, abstractmethod

from domain.entities.arxiv import ArxivPaperMetadataWithTranslatedUrl
from domain.value_objects import ArxivPaperId


class ITranslatedArxivRepository(ABC):
	"""Repository for persisting and retrieving translated arXiv paper metadata."""

	@abstractmethod
	async def find_by_paper_id(
		self, paper_id: ArxivPaperId
	) -> ArxivPaperMetadataWithTranslatedUrl | None:
		"""
		Find translated paper metadata by paper ID.

		Args:
		    paper_id: The arXiv paper ID.

		Returns:
		    The translated metadata, or None if not found.
		"""
		...

	@abstractmethod
	async def save(
		self, translated_paper_metadata: ArxivPaperMetadataWithTranslatedUrl
	) -> None:
		"""
		Save translated paper metadata.

		Args:
		    translated_paper_metadata: The metadata to save.
		"""
		...
