"""Delete a chat thread owned by the requesting user."""

import uuid
from logging import getLogger

from fastapi import HTTPException

from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork
from domain.errors.domain_error import ChatThreadNotFoundError


class DeleteChatThreadUseCase:
	def __init__(self, thread_uow: ChatThreadUnitOfWork) -> None:
		self._thread_uow = thread_uow
		self._logger = getLogger(__name__)

	async def execute(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> None:
		async with self._thread_uow as uow:
			try:
				thread = await uow.chat_thread_repository.find_by_id(thread_id)
			except ChatThreadNotFoundError as e:
				raise HTTPException(status_code=404, detail=str(e)) from e
			if thread.user_id != user_id:
				raise HTTPException(status_code=404, detail='Chat thread not found.')
			await uow.chat_thread_repository.delete(thread_id)
