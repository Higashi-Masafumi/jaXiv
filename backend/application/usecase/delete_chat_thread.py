"""Delete a chat thread owned by the requesting user."""

from logging import getLogger
from uuid import UUID

from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork
from domain.errors.domain_error import ChatThreadNotFoundError


class DeleteChatThreadUseCase:
	def __init__(self, thread_uow: ChatThreadUnitOfWork) -> None:
		self._thread_uow = thread_uow
		self._logger = getLogger(__name__)

	async def execute(self, thread_id: UUID, user_id: UUID) -> None:
		async with self._thread_uow as uow:
			thread = await uow.chat_thread_repository.find_by_id(thread_id)
			# 他ユーザーのスレッド存在を漏らさないため、所有者違いも 404 と同じエラーで返す。
			if thread.user_id != user_id:
				raise ChatThreadNotFoundError(str(thread_id))
			try:
				await uow.chat_thread_repository.delete(thread_id)
			except ChatThreadNotFoundError:
				# 並行リクエストで先に削除されたケースは成功扱いで吸収する。
				return
