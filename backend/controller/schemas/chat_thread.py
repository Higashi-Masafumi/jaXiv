"""Response schemas for chat thread history endpoints.

ドメイン層と同じ Anthropic 互換 content-block モデルを wire でも使う。
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from application.usecase import ChatDailyCount, ChatThreadSummary
from domain.entities.chat import ChatMessage, ChatThread, ContentBlock


class ChatThreadSummaryResponse(BaseModel):
	id: uuid.UUID
	paper_id: str
	created_at: datetime
	updated_at: datetime
	message_count: int
	title: str

	@classmethod
	def from_summary(cls, summary: ChatThreadSummary) -> 'ChatThreadSummaryResponse':
		return cls(
			id=summary.id,
			paper_id=summary.paper_id,
			created_at=summary.created_at,
			updated_at=summary.updated_at,
			message_count=summary.message_count,
			title=summary.title,
		)


class ChatThreadListResponse(BaseModel):
	threads: list[ChatThreadSummaryResponse]


class ChatMessageResponse(BaseModel):
	id: str
	role: Literal['user', 'assistant']
	content: list[ContentBlock]
	timestamp: datetime

	@classmethod
	def from_entity(cls, m: ChatMessage) -> 'ChatMessageResponse':
		return cls(
			id=m.id,
			role=m.role,
			content=list(m.content),
			timestamp=m.timestamp,
		)


class ChatThreadResponse(BaseModel):
	id: uuid.UUID
	paper_id: str
	created_at: datetime
	updated_at: datetime
	messages: list[ChatMessageResponse] = Field(default_factory=list)

	@classmethod
	def from_entity(cls, thread: ChatThread) -> 'ChatThreadResponse':
		return cls(
			id=thread.id,
			paper_id=thread.paper_id,
			created_at=thread.created_at,
			updated_at=thread.updated_at,
			messages=[ChatMessageResponse.from_entity(m) for m in thread.messages],
		)


class ChatDailyCountResponse(BaseModel):
	daily: int
	limit: int | None  # None means unlimited

	@classmethod
	def from_entity(cls, count: ChatDailyCount) -> 'ChatDailyCountResponse':
		return cls(daily=count.daily, limit=count.limit)
