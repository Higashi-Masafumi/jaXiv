import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.chat import ChatThread
from domain.value_objects.user_id import UserId


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

	@abstractmethod
	async def count_user_messages(self, user_id: UserId, since: datetime) -> int:
		"""Return the number of user-authored text messages since ``since``.

		"User-authored" excludes synthetic ``role='user'`` messages that only
		carry tool_result blocks (created by the agent itself).
		"""
		...
