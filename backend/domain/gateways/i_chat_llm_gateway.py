from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict

from domain.entities.chat import ChatMessage


class ToolDefinition(BaseModel):
	model_config = ConfigDict(frozen=True)

	name: str
	description: str
	parameters: dict[str, Any]


class ToolCallItem(BaseModel):
	model_config = ConfigDict(frozen=True)

	id: str
	name: str
	args: dict[str, Any]


class IChatLLMGateway(ABC):
	@abstractmethod
	def stream(
		self,
		messages: list[ChatMessage],
		tools: list[ToolDefinition],
		system_prompt: str,
	) -> AsyncIterator[str | list[ToolCallItem]]: ...
