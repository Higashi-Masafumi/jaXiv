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


class IChatLLMGateway(ABC):
    """Abstract gateway for LLM chat with tool-calling support.

    stream() yields str (text delta) or list[ToolCallItem] (tool calls).
    Tool calls are yielded as a single batch after the stream ends.
    """

    @abstractmethod
    def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> AsyncIterator[str | list[ToolCallItem]]: ...
