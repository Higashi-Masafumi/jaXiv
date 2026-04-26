from abc import abstractmethod

from domain.repositories import IChatThreadRepository

from ._base import UnitOfWork


class ChatThreadUnitOfWork(UnitOfWork):
	"""チャットスレッドの永続化用 UoW。"""

	@property
	@abstractmethod
	def chat_thread_repository(self) -> IChatThreadRepository:
		raise NotImplementedError
