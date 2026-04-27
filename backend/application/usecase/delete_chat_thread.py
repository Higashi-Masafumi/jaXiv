"""Delete a chat thread owned by the requesting user.

RLS により他人のスレッドは DELETE 対象から除外されるため、所有者の明示チェックは不要。
存在しない／他人の／既に削除済み の全ケースを idempotent に成功扱いする。
"""

from logging import getLogger
from uuid import UUID

from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork
from domain.errors.domain_error import ChatThreadNotFoundError


class DeleteChatThreadUseCase:
	def __init__(self, thread_uow: ChatThreadUnitOfWork) -> None:
		self._thread_uow = thread_uow
		self._logger = getLogger(__name__)

	async def execute(self, thread_id: UUID) -> None:
		async with self._thread_uow as uow:
			try:
				await uow.chat_thread_repository.delete(thread_id)
			except ChatThreadNotFoundError:
				return
