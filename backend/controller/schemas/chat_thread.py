"""Response schemas for chat thread history endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from application.usecase import ChatThreadSummary
from domain.entities.chat import ChatMessage, ChatThread


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


class ChatToolCallResponse(BaseModel):
	id: str
	name: str
	args: dict[str, Any]


class ChatMessageResponse(BaseModel):
	id: str
	role: str
	content: str | None = None
	tool_calls: list[ChatToolCallResponse] | None = None
	tool_call_id: str | None = None
	name: str | None = None
	timestamp: datetime

	@classmethod
	def from_entity(cls, m: ChatMessage) -> 'ChatMessageResponse':
		return cls(
			id=m.id,
			role=m.role,
			content=m.content,
			tool_calls=[
				ChatToolCallResponse(id=tc.id, name=tc.name, args=tc.args)
				for tc in (m.tool_calls or [])
			]
			if m.tool_calls
			else None,
			tool_call_id=m.tool_call_id,
			name=m.name,
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
