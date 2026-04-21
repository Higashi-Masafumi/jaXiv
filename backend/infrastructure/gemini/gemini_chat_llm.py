import json
import uuid
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from google import genai
from google.genai import types

from domain.gateways.i_chat_llm_gateway import (
    IChatLLMGateway,
    ToolCallItem,
    ToolDefinition,
)
from infrastructure.gemini.config import get_gemini_config


class GeminiChatLLM(IChatLLMGateway):
    def __init__(self, model: str = 'gemini-3-flash-preview') -> None:
        self._client = genai.Client(
            api_key=get_gemini_config().gemini_api_key.get_secret_value()
        )
        self._model = model
        self._logger = getLogger(__name__)

    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> AsyncIterator[str | list[ToolCallItem]]:
        # Convert messages to Gemini Content objects
        contents: list[types.Content] = []
        for msg in messages:
            role = msg['role']
            if role == 'user':
                contents.append(
                    types.Content(role='user', parts=[types.Part.from_text(text=msg['content'])])
                )
            elif role == 'assistant':
                parts: list[types.Part] = []
                if msg.get('tool_calls'):
                    for tc in msg['tool_calls']:
                        parts.append(types.Part.from_function_call(name=tc['name'], args=tc['args']))
                elif msg.get('content'):
                    parts.append(types.Part.from_text(text=msg['content']))
                if parts:
                    contents.append(types.Content(role='model', parts=parts))
            elif role == 'tool':
                contents.append(
                    types.Content(
                        role='user',
                        parts=[
                            types.Part.from_function_response(
                                name=msg.get('name', 'tool'),
                                response={'result': json.loads(msg['content'])},
                            )
                        ],
                    )
                )

        # Build Gemini tool config
        gemini_tools: list[types.Tool] | None = None
        if tools:
            gemini_tools = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=td.name,
                            description=td.description,
                            parameters=td.parameters,  # type: ignore[arg-type]
                        )
                        for td in tools
                    ]
                )
            ]

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=gemini_tools,  # type: ignore[arg-type]
        )

        tool_call_parts: list[Any] = []
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,  # type: ignore[arg-type]
            config=config,
        ):
            parts_in_chunk = (
                chunk.candidates[0].content.parts
                if chunk.candidates and chunk.candidates[0].content
                else None
            ) or []
            for part in parts_in_chunk:
                if part.function_call is not None:
                    tool_call_parts.append(part.function_call)
            if chunk.text:
                yield chunk.text

        if tool_call_parts:
            yield [
                ToolCallItem(
                    id=str(uuid.uuid4()),
                    name=fc.name,  # type: ignore[union-attr,arg-type]
                    args=dict(fc.args),  # type: ignore[union-attr,arg-type]
                )
                for fc in tool_call_parts
            ]
