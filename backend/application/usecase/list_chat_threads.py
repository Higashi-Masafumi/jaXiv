"""List chat threads belonging to the requesting user for a given paper."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from domain.entities.chat import ChatThread, TextBlock
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
		raw = ''
		for m in thread.messages:
			if m.role != 'user':
				continue
			text_block = next((b for b in m.content if isinstance(b, TextBlock) and b.text), None)
			if text_block is not None:
				raw = text_block.text
				break
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

	async def execute(self, paper_id: str, user_id: UUID) -> list[ChatThreadSummary]:
		threads = await self._chat_thread_repository.find_by_paper_id(paper_id, user_id)
		# 表示にはメッセージ未送信のスレッド（タイトル未確定）を除外する。
		return [ChatThreadSummary.from_thread(t) for t in threads if len(t.messages) > 0]
