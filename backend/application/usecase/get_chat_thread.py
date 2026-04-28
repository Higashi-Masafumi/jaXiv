"""Get a single chat thread (with full message history) for the requesting user.

RLS により他人のスレッドは SELECT で見えないため、ここで所有者チェックは行わない。
"""

from uuid import UUID

from domain.entities.chat import ChatThread
from domain.repositories import IChatThreadRepository


class GetChatThreadUseCase:
	def __init__(self, chat_thread_repository: IChatThreadRepository) -> None:
		self._chat_thread_repository = chat_thread_repository

	async def execute(self, thread_id: UUID) -> ChatThread:
		return await self._chat_thread_repository.find_by_id(thread_id)
