"""List chat threads belonging to the requesting user for a given paper.

RLS により他人のスレッドは SELECT で見えないため、user_id フィルタは不要。
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from domain.entities.chat import ChatThread
from domain.repositories import IChatThreadRepository


SNIPPET_MAX_LENGTH = 80


class ChatThreadSummary(BaseModel):
	id: UUID
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
	def __init__(self, chat_thread_repository: IChatThreadRepository) -> None:
		self._chat_thread_repository = chat_thread_repository

	async def execute(self, paper_id: str) -> list[ChatThreadSummary]:
		threads = await self._chat_thread_repository.find_by_paper_id(paper_id)
		# 表示にはメッセージ未送信のスレッド（タイトル未確定）を除外する。
		return [ChatThreadSummary.from_thread(t) for t in threads if len(t.messages) > 0]
