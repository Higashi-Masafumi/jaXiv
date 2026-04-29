import uuid
from collections.abc import AsyncIterator
from logging import getLogger

from google import genai
from google.genai import types

from domain.entities.chat import ChatMessage, TextBlock, ToolResultBlock, ToolUseBlock
from domain.gateways.i_chat_llm_gateway import (
	IChatLLMGateway,
	LLMStreamEvent,
	LLMTextDelta,
	LLMToolUse,
	ToolDefinition,
)
from infrastructure.gemini.config import get_gemini_config


class GeminiChatLLM(IChatLLMGateway):
	def __init__(self, model: str = 'gemini-2.5-flash') -> None:
		self._client = genai.Client(api_key=get_gemini_config().gemini_api_key.get_secret_value())
		self._model = model
		self._logger = getLogger(__name__)

	def _to_contents(self, messages: list[ChatMessage]) -> list[types.Content]:
		"""ContentBlock ベースのメッセージを Gemini の Content/Part に変換する。

		- assistant の text/tool_use ブロックは role='model' の単一 Content にまとめる
		- user の text ブロックは role='user' の単一 Content にまとめる
		- user の tool_result ブロックは Gemini では function_response Part として
		  role='user' Content に詰め込む（複数 tool_result を 1 Content に集約可）
		"""
		contents: list[types.Content] = []
		for msg in messages:
			parts: list[types.Part] = []
			if msg.role == 'assistant':
				for block in msg.content:
					if isinstance(block, TextBlock):
						if block.text:
							parts.append(types.Part.from_text(text=block.text))
					elif isinstance(block, ToolUseBlock):
						parts.append(
							types.Part(
								function_call=types.FunctionCall(
									name=block.name,
									args=block.input,
								)
							)
						)
				if parts:
					contents.append(types.Content(role='model', parts=parts))
			else:  # user
				for block in msg.content:
					if isinstance(block, TextBlock):
						if block.text:
							parts.append(types.Part.from_text(text=block.text))
					elif isinstance(block, ToolResultBlock):
						parts.append(
							types.Part.from_function_response(
								name=block.name,
								response=block.content,
							)
						)
				if parts:
					contents.append(types.Content(role='user', parts=parts))
		return contents

	async def stream(
		self,
		messages: list[ChatMessage],
		tools: list[ToolDefinition],
		system_prompt: str,
	) -> AsyncIterator[LLMStreamEvent]:
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

		pending_tool_uses: list[LLMToolUse] = []
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
					pending_tool_uses.append(
						LLMToolUse(
							id=str(uuid.uuid4()),
							name=part.function_call.name or '',
							input=dict(part.function_call.args or {}),
						)
					)
			if chunk.text:
				yield LLMTextDelta(text=chunk.text)

		for tu in pending_tool_uses:
			yield tu
