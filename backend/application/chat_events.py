"""SSE event protocol for chat streaming.

Anthropic Messages API のストリーミング形式に準拠する。
content-block の型 (TextBlock / ToolUseBlock / ToolResultBlock) は
ドメインエンティティと共有することで、永続化・SSE・API・UI の
4層を同じ shape で扱う。

  MessageStartEvent -> 新しいメッセージの開始（role 通知）
  BlockStartEvent   -> 新しい content block の開始
  BlockDeltaEvent   -> 既存ブロックへの追記（text の差分）
  BlockStopEvent    -> 現在ブロックの終了
  ThreadIdEvent     -> 最初に送る、このストリームのスレッド ID
  MessageStopEvent  -> ストリーム終了
  ErrorEvent        -> エラー
"""

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.chat import ContentBlock, TextBlock, ToolResultBlock, ToolUseBlock

__all__ = [
	'BlockDeltaEvent',
	'BlockStartEvent',
	'BlockStopEvent',
	'ChatRequest',
	'ChatStreamEvent',
	'ErrorEvent',
	'MessageStartEvent',
	'MessageStopEvent',
	'TextBlock',
	'TextDelta',
	'ThreadIdEvent',
	'ToolResultBlock',
	'ToolUseBlock',
]


# ---------------------------------------------------------------------------
# Delta types (inside BlockDeltaEvent)
# ---------------------------------------------------------------------------


class TextDelta(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['text_delta'] = 'text_delta'
	text: str


# ---------------------------------------------------------------------------
# Top-level stream events
# ---------------------------------------------------------------------------


class ThreadIdEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['thread_id'] = 'thread_id'
	thread_id: str


class MessageStartEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['message_start'] = 'message_start'
	message_id: str
	role: Literal['user', 'assistant']


class BlockStartEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['block_start'] = 'block_start'
	index: int
	block: ContentBlock


class BlockDeltaEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['block_delta'] = 'block_delta'
	index: int
	delta: TextDelta


class BlockStopEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['block_stop'] = 'block_stop'
	index: int


class MessageStopEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['message_stop'] = 'message_stop'


class ErrorEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['error'] = 'error'
	message: str
	error_details: str | None = None


ChatStreamEvent = Annotated[
	ThreadIdEvent
	| MessageStartEvent
	| BlockStartEvent
	| BlockDeltaEvent
	| BlockStopEvent
	| MessageStopEvent
	| ErrorEvent,
	Field(discriminator='type'),
]


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
	message: str = Field(description='User message text')
	thread_id: uuid.UUID | None = Field(default=None, description='Existing thread ID to continue')
