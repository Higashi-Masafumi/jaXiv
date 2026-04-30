import uuid
from abc import ABC, abstractmethod

from domain.entities.chat import ChatThread


class IChatThreadRepository(ABC):
	@abstractmethod
	async def find_by_id(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> ChatThread: ...

	@abstractmethod
	async def update(self, thread: ChatThread) -> None: ...

	@abstractmethod
	async def create(self, paper_id: str, user_id: uuid.UUID) -> ChatThread: ...

	@abstractmethod
	async def find_by_paper_id(
		self, paper_id: str, user_id: uuid.UUID
	) -> list[ChatThread]: ...

	@abstractmethod
	async def delete(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> None: ...
