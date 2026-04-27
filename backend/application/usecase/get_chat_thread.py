"""Get a single chat thread (with full message history) for the requesting user."""

from logging import getLogger
from uuid import UUID

from domain.entities.chat import ChatThread
from domain.errors.domain_error import ChatThreadNotFoundError
from domain.repositories import IChatThreadRepository


class GetChatThreadUseCase:
	def __init__(self, chat_thread_repository: IChatThreadRepository) -> None:
		self._chat_thread_repository = chat_thread_repository
		self._logger = getLogger(__name__)

	async def execute(self, thread_id: UUID, user_id: UUID) -> ChatThread:
		thread = await self._chat_thread_repository.find_by_id(thread_id)
		# 他ユーザーのスレッド存在を漏らさないため、所有者違いも 404 と同じエラーで返す。
		if thread.user_id != user_id:
			raise ChatThreadNotFoundError(str(thread_id))
		return thread
