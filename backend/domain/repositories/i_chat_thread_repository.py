import uuid
from abc import ABC, abstractmethod

from domain.entities.chat import ChatThread


class IChatThreadRepository(ABC):
	"""Repository for persisting and retrieving chat threads."""

	@abstractmethod
	async def find_by_id(self, thread_id: uuid.UUID) -> ChatThread | None: ...

	@abstractmethod
	async def find_by_id_and_user(
		self, thread_id: uuid.UUID, user_id: uuid.UUID
	) -> ChatThread | None: ...

	@abstractmethod
	async def save(self, thread: ChatThread) -> None: ...

	@abstractmethod
	async def create(self, paper_id: str, user_id: uuid.UUID) -> ChatThread: ...
