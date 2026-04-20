from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ConfigDict


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


class LLMResponse(BaseModel):
    text: str | None = None
    tool_calls: list[ToolCallItem] | None = None


class IChatLLMGateway(ABC):
    """Abstract gateway for LLM chat with tool-calling support."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> LLMResponse: ...

    @abstractmethod
    def stream_text(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str,
    ) -> AsyncIterator[str]: ...
