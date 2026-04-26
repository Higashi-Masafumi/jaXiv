"""Pydantic schemas for the chat API.

Stream event protocol is inspired by Anthropic's streaming format:
  BlockStartEvent  -> a new content block begins (text or tool_use)
  BlockDeltaEvent  -> incremental update to the current block
  BlockStopEvent   -> the current block ends
  ToolResultEvent  -> backend executed a tool and returns the result
  ThreadIdEvent    -> emitted first, carries the thread_id for the session
  MessageStopEvent -> final event, stream is complete
  ErrorEvent       -> an error occurred
"""

import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Block types (inside BlockStartEvent)
# ---------------------------------------------------------------------------


class TextBlock(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['text'] = 'text'


class ToolUseBlock(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['tool_use'] = 'tool_use'
	id: str
	name: str
	input: dict[str, Any] = Field(default_factory=dict)


Block = Annotated[TextBlock | ToolUseBlock, Field(discriminator='type')]


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


class BlockStartEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['block_start'] = 'block_start'
	index: int
	block: Block


class BlockDeltaEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['block_delta'] = 'block_delta'
	index: int
	delta: TextDelta


class BlockStopEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['block_stop'] = 'block_stop'
	index: int


class ToolResultEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['tool_result'] = 'tool_result'
	tool_use_id: str
	name: str
	content: dict[str, Any]


class MessageStopEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['message_stop'] = 'message_stop'


class ErrorEvent(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['error'] = 'error'
	message: str


ChatStreamEvent = Annotated[
	ThreadIdEvent
	| BlockStartEvent
	| BlockDeltaEvent
	| BlockStopEvent
	| ToolResultEvent
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
