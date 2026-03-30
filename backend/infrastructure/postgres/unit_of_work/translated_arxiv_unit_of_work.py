from application.unit_of_works import TranslatedArxivUnitOfWork
from domain.repositories import ITranslatedArxivRepository
from infrastructure.postgres.repositories import PostgresTranslatedArxivRepository

from ._base import SqlAlchemyUnitOfWorkBase


class PostgresTranslatedArxivUnitOfWork(SqlAlchemyUnitOfWorkBase, TranslatedArxivUnitOfWork):
	@property
	def translated_arxiv_repository(self) -> ITranslatedArxivRepository:
		return PostgresTranslatedArxivRepository(session=self._session)
