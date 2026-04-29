from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.entities.chat import ChatMessage


class ToolDefinition(BaseModel):
	model_config = ConfigDict(frozen=True)

	name: str
	description: str
	parameters: dict[str, Any]


class LLMTextDelta(BaseModel):
	"""LLM が生成した assistant テキストの差分。"""

	model_config = ConfigDict(frozen=True)
	type: Literal['text_delta'] = 'text_delta'
	text: str


class LLMToolUse(BaseModel):
	"""LLM が呼び出したい tool（input は確定済み）。"""

	model_config = ConfigDict(frozen=True)
	type: Literal['tool_use'] = 'tool_use'
	id: str
	name: str
	input: dict[str, Any]


LLMStreamEvent = Annotated[LLMTextDelta | LLMToolUse, Field(discriminator='type')]


class IChatLLMGateway(ABC):
	@abstractmethod
	def stream(
		self,
		messages: list[ChatMessage],
		tools: list[ToolDefinition],
		system_prompt: str,
	) -> AsyncIterator[LLMStreamEvent]: ...
