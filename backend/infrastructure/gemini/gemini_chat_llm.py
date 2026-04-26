import json
import uuid
from collections.abc import AsyncIterator
from logging import getLogger

from google import genai
from google.genai import types

from domain.entities.chat import ChatMessage
from domain.gateways.i_chat_llm_gateway import (
	IChatLLMGateway,
	ToolCallItem,
	ToolDefinition,
)
from infrastructure.gemini.config import get_gemini_config


class GeminiChatLLM(IChatLLMGateway):
	def __init__(self, model: str = 'gemini-2.5-flash') -> None:
		self._client = genai.Client(api_key=get_gemini_config().gemini_api_key.get_secret_value())
		self._model = model
		self._logger = getLogger(__name__)
		self._fc_parts_by_id: dict[str, types.Part] = {}

	def _to_contents(self, messages: list[ChatMessage]) -> list[types.Content]:
		contents: list[types.Content] = []
		for msg in messages:
			if msg.role == 'user':
				contents.append(
					types.Content(role='user', parts=[types.Part.from_text(text=msg.content or '')])
				)
			elif msg.role == 'assistant':
				parts: list[types.Part] = []
				if msg.tool_calls:
					for tc in msg.tool_calls:
						cached = self._fc_parts_by_id.get(tc.id)
						if cached:
							parts.append(cached)
						else:
							parts.append(
								types.Part.from_text(
									text=f'[Called {tc.name}({json.dumps(tc.args, ensure_ascii=False)})]'
								)
							)
				elif msg.content:
					parts.append(types.Part.from_text(text=msg.content))
				if parts:
					contents.append(types.Content(role='model', parts=parts))
			elif msg.role == 'tool':
				if msg.tool_call_id and msg.tool_call_id in self._fc_parts_by_id:
					contents.append(
						types.Content(
							role='user',
							parts=[
								types.Part.from_function_response(
									name=msg.name or 'tool',
									response={'result': json.loads(msg.content or '{}')},
								)
							],
						)
					)
				else:
					contents.append(
						types.Content(
							role='user',
							parts=[
								types.Part.from_text(
									text=f'[Result of {msg.name or "tool"}]: {msg.content}'
								)
							],
						)
					)
		return contents

	async def stream(
		self,
		messages: list[ChatMessage],
		tools: list[ToolDefinition],
		system_prompt: str,
	) -> AsyncIterator[str | list[ToolCallItem]]:
		contents = self._to_contents(messages)

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

		tool_call_parts: list[tuple[str, types.Part]] = []
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
					tc_id = str(uuid.uuid4())
					tool_call_parts.append((tc_id, part))
			if chunk.text:
				yield chunk.text

		if tool_call_parts:
			for tc_id, part in tool_call_parts:
				self._fc_parts_by_id[tc_id] = part
			yield [
				ToolCallItem(
					id=tc_id,
					name=part.function_call.name,  # type: ignore[union-attr,arg-type]
					args=dict(part.function_call.args),  # type: ignore[union-attr,arg-type]
				)
				for tc_id, part in tool_call_parts
			]
