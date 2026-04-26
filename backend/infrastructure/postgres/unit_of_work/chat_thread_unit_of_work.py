from application.unit_of_works import ChatThreadUnitOfWork
from domain.repositories import IChatThreadRepository
from infrastructure.postgres.repositories import PostgresChatThreadRepository

from ._base import SqlAlchemyUnitOfWorkBase


class PostgresChatThreadUnitOfWork(SqlAlchemyUnitOfWorkBase, ChatThreadUnitOfWork):
	@property
	def chat_thread_repository(self) -> IChatThreadRepository:
		return PostgresChatThreadRepository(session=self._session)
