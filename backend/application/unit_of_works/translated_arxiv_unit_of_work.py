from abc import abstractmethod

from domain.repositories import ITranslatedArxivRepository

from ._base import UnitOfWork


class TranslatedArxivUnitOfWork(UnitOfWork):
	"""翻訳済み arXiv メタデータの永続化用 UoW。"""

	@property
	@abstractmethod
	def translated_arxiv_repository(self) -> ITranslatedArxivRepository:
		raise NotImplementedError
