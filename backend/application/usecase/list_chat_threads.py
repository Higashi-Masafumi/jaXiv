"""List chat threads belonging to a user for a given paper."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork
from domain.entities.chat import ChatThread


SNIPPET_MAX_LENGTH = 80


class ChatThreadSummary(BaseModel):
	id: uuid.UUID
	paper_id: str
	created_at: datetime
	updated_at: datetime
	message_count: int
	title: str

	@classmethod
	def from_thread(cls, thread: ChatThread) -> 'ChatThreadSummary':
		first_user_message = next(
			(m for m in thread.messages if m.role == 'user' and m.content),
			None,
		)
		raw = (first_user_message.content if first_user_message else '') or ''
		title = raw.strip().splitlines()[0] if raw.strip() else '新しいチャット'
		if len(title) > SNIPPET_MAX_LENGTH:
			title = title[:SNIPPET_MAX_LENGTH] + '…'
		return cls(
			id=thread.id,
			paper_id=thread.paper_id,
			created_at=thread.created_at,
			updated_at=thread.updated_at,
			message_count=len(thread.messages),
			title=title,
		)


class ListChatThreadsUseCase:
	def __init__(self, thread_uow: ChatThreadUnitOfWork) -> None:
		self._thread_uow = thread_uow

	async def execute(self, paper_id: str, user_id: uuid.UUID) -> list[ChatThreadSummary]:
		async with self._thread_uow as uow:
			threads = await uow.chat_thread_repository.find_by_paper_and_user(
				paper_id=paper_id, user_id=user_id
			)
			return [ChatThreadSummary.from_thread(t) for t in threads if len(t.messages) > 0]
