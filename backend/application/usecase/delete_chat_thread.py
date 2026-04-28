"""Delete a chat thread owned by the requesting user.

RLS により他人のスレッドは DELETE 対象から除外されるため、所有者の明示チェックは不要。
存在しない場合は ChatThreadNotFoundError がそのまま伝播し、middleware で 404 に変換される。
"""

from uuid import UUID

from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork


class DeleteChatThreadUseCase:
	def __init__(self, thread_uow: ChatThreadUnitOfWork) -> None:
		self._thread_uow = thread_uow

	async def execute(self, thread_id: UUID) -> None:
		async with self._thread_uow as uow:
			await uow.chat_thread_repository.delete(thread_id)
