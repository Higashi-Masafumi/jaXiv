"""Chat domain entities.

Anthropic Messages API 互換の content-block モデルを採用する。

  Message      = { role: 'user' | 'assistant', content: ContentBlock[] }
  ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock

tool_result は OpenAI 形式の独立 role ではなく、Anthropic に倣って
**user-role メッセージ** の content の中に置く。これにより:
- text と tool_use の順序が配列で保たれる
- 永続化・SSE・API・UI の各層で同じ content-block を使える
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TextBlock(BaseModel):
	"""Anthropic 互換の text content block。`type` は OpenAPI で required にする
	ため敢えてデフォルト値を持たせず、コンストラクタで明示的に指定する運用とする。
	"""

	model_config = ConfigDict(frozen=True)
	type: Literal['text']
	text: str

	def __init__(self, **data: Any) -> None:
		data.setdefault('type', 'text')
		super().__init__(**data)


class ToolUseBlock(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['tool_use']
	id: str
	name: str
	input: dict[str, Any] = Field(default_factory=dict)

	def __init__(self, **data: Any) -> None:
		data.setdefault('type', 'tool_use')
		super().__init__(**data)


class ToolResultBlock(BaseModel):
	model_config = ConfigDict(frozen=True)
	type: Literal['tool_result']
	tool_use_id: str
	name: str
	content: dict[str, Any]
	is_error: bool = False

	def __init__(self, **data: Any) -> None:
		data.setdefault('type', 'tool_result')
		super().__init__(**data)


ContentBlock = Annotated[
	TextBlock | ToolUseBlock | ToolResultBlock,
	Field(discriminator='type'),
]


class ChatMessage(BaseModel):
	id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	role: Literal['user', 'assistant']
	content: list[ContentBlock] = Field(default_factory=list)
	timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatThread(BaseModel):
	id: uuid.UUID = Field(default_factory=uuid.uuid4)
	paper_id: str
	user_id: uuid.UUID
	messages: list[ChatMessage] = Field(default_factory=list)
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
