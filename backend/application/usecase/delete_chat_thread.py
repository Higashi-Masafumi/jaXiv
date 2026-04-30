"""Delete a chat thread owned by the requesting user.

存在しない、または所有者でない場合は ChatThreadNotFoundError がそのまま伝播し、
middleware で 404 に変換される。
"""

from uuid import UUID

from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork


class DeleteChatThreadUseCase:
	def __init__(self, thread_uow: ChatThreadUnitOfWork) -> None:
		self._thread_uow = thread_uow

	async def execute(self, thread_id: UUID, user_id: UUID) -> None:
		async with self._thread_uow as uow:
			await uow.chat_thread_repository.delete(thread_id, user_id)
