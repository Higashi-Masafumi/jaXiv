"""Agentic chat use case: routes user messages to Gemini with RAG tool support."""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from logging import getLogger

from application.chat_events import (
	BlockDeltaEvent,
	BlockStartEvent,
	BlockStopEvent,
	ChatStreamEvent,
	ErrorEvent,
	MessageStopEvent,
	TextBlock,
	TextDelta,
	ThreadIdEvent,
	ToolResultEvent,
	ToolUseBlock,
)
from domain.entities.chat import ChatMessage, ToolCall
from domain.gateways.i_chat_llm_gateway import IChatLLMGateway, ToolCallItem, ToolDefinition
from domain.repositories.i_chat_thread_repository import IChatThreadRepository

from .rag_search_image import RagSearchImageUseCase
from .rag_search_text import RagSearchTextUseCase

SYSTEM_PROMPT = """\
あなたは論文の内容についての質問に答えるアシスタントです。
論文内容を検索するツールを使用して事実に基づいた正確な回答を行なってください。
回答はマークダウン形式で記述してください。
数式はKaTeX形式（ブロック数式は $$...$$ 、インライン数式は $...$ ）で記述してください。
"""

RAG_TOOLS: list[ToolDefinition] = [
	ToolDefinition(
		name='textSearch',
		description='論文本文チャンクの意味的検索。要約・定義・手法の説明などテキストに関する質問に使う。',
		parameters={
			'type': 'object',
			'properties': {'query': {'type': 'string', 'description': '検索クエリ（自然言語）'}},
			'required': ['query'],
		},
	),
	ToolDefinition(
		name='imageSearch',
		description='図・画像に関連する検索。キャプションの意味で近い図の画像URLを返す。図やスクリーンショットの話題に使う。',
		parameters={
			'type': 'object',
			'properties': {'query': {'type': 'string', 'description': '検索クエリ（自然言語）'}},
			'required': ['query'],
		},
	),
]

MAX_TOOL_ROUNDS = 3


class ChatWithPaperUseCase:
	def __init__(
		self,
		llm: IChatLLMGateway,
		thread_repo: IChatThreadRepository,
		rag_text: RagSearchTextUseCase,
		rag_image: RagSearchImageUseCase,
	) -> None:
		self._llm = llm
		self._thread_repo = thread_repo
		self._rag_text = rag_text
		self._rag_image = rag_image
		self._logger = getLogger(__name__)

	async def execute(
		self,
		paper_id: str,
		message: str,
		thread_id: uuid.UUID | None,
		user_id: uuid.UUID,
	) -> AsyncIterator[ChatStreamEvent]:
		if thread_id:
			thread = await self._thread_repo.find_by_id(thread_id)
		else:
			thread = await self._thread_repo.create(paper_id, user_id)

		yield ThreadIdEvent(thread_id=str(thread.id))
		thread.messages.append(ChatMessage(role='user', content=message))

		block_index = 0

		try:
			# tool callループ（最大MAX_TOOL_ROUNDS回）
			for _ in range(MAX_TOOL_ROUNDS):
				tool_calls: list[ToolCallItem] = []
				async for chunk in self._llm.stream(thread.messages, RAG_TOOLS, SYSTEM_PROMPT):
					if isinstance(chunk, list):
						tool_calls = chunk

				if not tool_calls:
					break

				thread.messages.append(
					ChatMessage(
						role='assistant',
						tool_calls=[
							ToolCall(id=tc.id, name=tc.name, args=tc.args) for tc in tool_calls
						],
					)
				)
				for tc in tool_calls:
					yield BlockStartEvent(
						index=block_index,
						block=ToolUseBlock(id=tc.id, name=tc.name),
					)
					yield BlockStopEvent(index=block_index)
					block_index += 1

					query = tc.args.get('query', '')
					if tc.name == 'textSearch':
						tool_result = await self._rag_text.execute(paper_id, query)
						yield ToolResultEvent(
							tool_use_id=tc.id, name=tc.name, content=tool_result.model_dump()
						)
					elif tc.name == 'imageSearch':
						tool_result = await self._rag_image.execute(paper_id, query)
						yield ToolResultEvent(
							tool_use_id=tc.id, name=tc.name, content=tool_result.model_dump()
						)
					else:
						yield ToolResultEvent(
							tool_use_id=tc.id,
							name=tc.name,
							content={'error': f'Unknown tool: {tc.name}'},
						)
					thread.messages.append(
						ChatMessage(
							role='tool',
							content=json.dumps(tool_result, ensure_ascii=False),
							tool_call_id=tc.id,
							name=tc.name,
						)
					)

			# 最終応答（toolなし）
			yield BlockStartEvent(index=block_index, block=TextBlock())
			accumulated = ''
			async for chunk in self._llm.stream(thread.messages, [], SYSTEM_PROMPT):
				if isinstance(chunk, list):
					continue
				accumulated += chunk
				yield BlockDeltaEvent(index=block_index, delta=TextDelta(text=chunk))

			yield BlockStopEvent(index=block_index)
			thread.messages.append(ChatMessage(role='assistant', content=accumulated))

		except Exception as e:
			self._logger.exception('Chat error for paper %s', paper_id)
			yield ErrorEvent(message=str(e))
			return

		thread.updated_at = datetime.now(UTC)
		await self._thread_repo.update(thread)
		yield MessageStopEvent()
