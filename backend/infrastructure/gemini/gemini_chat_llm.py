import json
import logging
import uuid
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from domain.gateways.i_chat_llm_gateway import (
    IChatLLMGateway,
    LLMResponse,
    ToolCallItem,
    ToolDefinition,
)
from infrastructure.gemini.config import get_gemini_config


class GeminiChatLLM(IChatLLMGateway):
    """Chat LLM gateway backed by Gemini."""

    def __init__(self, model: str = 'gemini-3-flash-preview') -> None:
        self._client = genai.Client(
            api_key=get_gemini_config().gemini_api_key.get_secret_value()
        )
        self._model = model
        self._logger = getLogger(__name__)

    @staticmethod
    def _to_contents(messages: list[dict[str, Any]]) -> list[types.Content]:
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
                        parts.append(
                            types.Part.from_function_call(name=tc['name'], args=tc['args'])
                        )
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
        return contents

    @staticmethod
    def _to_gemini_tools(tool_defs: list[ToolDefinition]) -> list[types.Tool] | None:
        if not tool_defs:
            return None
        declarations = [
            types.FunctionDeclaration(
                name=td.name,
                description=td.description,
                parameters=td.parameters,  # type: ignore[arg-type]
            )
            for td in tool_defs
        ]
        return [types.Tool(function_declarations=declarations)]

    async def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> LLMResponse:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=self._to_gemini_tools(tools),  # type: ignore[arg-type]
        )
        response = await self._generate_with_retry(
            model=self._model,
            contents=self._to_contents(messages),
            config=config,
        )

        if not response.candidates:
            return LLMResponse(text='')
        candidate = response.candidates[0]
        parts = (candidate.content.parts if candidate.content else None) or []

        func_calls = [p for p in parts if p.function_call is not None]
        if func_calls:
            return LLMResponse(
                tool_calls=[
                    ToolCallItem(
                        id=str(uuid.uuid4()),
                        name=fc.function_call.name,  # type: ignore[union-attr,arg-type]
                        args=dict(fc.function_call.args),  # type: ignore[union-attr,arg-type]
                    )
                    for fc in func_calls
                ]
            )

        return LLMResponse(text=response.text or '')

    async def stream_text(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str,
    ) -> AsyncIterator[str]:
        config = types.GenerateContentConfig(system_instruction=system_prompt)
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=self._to_contents(messages),  # type: ignore[arg-type]
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    async def _generate_with_retry(self, **kwargs: Any) -> types.GenerateContentResponse:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(genai_errors.ServerError),
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=2, max=16),
            before_sleep=before_sleep_log(self._logger, logging.WARNING),
            reraise=True,
        ):
            with attempt:
                return await self._client.aio.models.generate_content(**kwargs)  # type: ignore[arg-type]
        raise RuntimeError('Unreachable')  # pragma: no cover
