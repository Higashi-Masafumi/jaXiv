"""Agentic chat use case: routes user messages to Gemini with RAG tool support."""

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
from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork
from domain.entities.chat import ChatMessage, ToolCall
from domain.gateways.i_chat_llm_gateway import IChatLLMGateway, ToolCallItem, ToolDefinition

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
		description='論文本文チャンクの意味的検索。要約・定義・手法の説明などテキストに関する質問に使う。queryは英語で指定する。',
		parameters={
			'type': 'object',
			'properties': {'query': {'type': 'string', 'description': '検索クエリ（自然言語）'}},
			'required': ['query'],
		},
	),
	ToolDefinition(
		name='imageSearch',
		description='図・画像に関連する検索。キャプションの意味で近い図の画像URLを返す。図やスクリーンショットの話題に使う。queryは英語で指定する。',
		parameters={
			'type': 'object',
			'properties': {'query': {'type': 'string', 'description': '検索クエリ（自然言語）'}},
			'required': ['query'],
		},
	),
]

MAX_TOOL_ROUNDS = 3
MAX_CONVERSATION_TURNS = 10


class ChatWithPaperUseCase:
	def __init__(
		self,
		llm: IChatLLMGateway,
		thread_uow: ChatThreadUnitOfWork,
		rag_text: RagSearchTextUseCase,
		rag_image: RagSearchImageUseCase,
	) -> None:
		self._llm = llm
		self._thread_uow = thread_uow
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
		try:
			async with self._thread_uow as uow:
				repo = uow.chat_thread_repository
				if thread_id:
					thread = await repo.find_by_id(thread_id)
				else:
					thread = await repo.create(paper_id, user_id)

				yield ThreadIdEvent(thread_id=str(thread.id))
				thread.messages.append(ChatMessage(role='user', content=message))

				block_index = 0
				accumulated = ''

				# tool callループ（最大MAX_TOOL_ROUNDS回）
				for _ in range(MAX_TOOL_ROUNDS):
					tool_calls: list[ToolCallItem] = []
					iteration_text = ''
					user_indices = [i for i, m in enumerate(thread.messages) if m.role == 'user']
					cut_at = (
						user_indices[-MAX_CONVERSATION_TURNS]
						if len(user_indices) > MAX_CONVERSATION_TURNS
						else 0
					)
					context = thread.messages[cut_at:]
					yield BlockStartEvent(index=block_index, block=TextBlock())
					async for chunk in self._llm.stream(context, RAG_TOOLS, SYSTEM_PROMPT):
						if isinstance(chunk, list):
							tool_calls = chunk
						else:
							yield BlockDeltaEvent(index=block_index, delta=TextDelta(text=chunk))
							iteration_text += chunk
					yield BlockStopEvent(index=block_index)
					block_index += 1

					if not tool_calls:
						accumulated = iteration_text
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
							block=ToolUseBlock(id=tc.id, name=tc.name, input=tc.args),
						)
						yield BlockStopEvent(index=block_index)
						block_index += 1

						query = tc.args.get('query', '')
						if tc.name == 'textSearch':
							text_search_result = await self._rag_text.execute(paper_id, query)
							yield ToolResultEvent(
								tool_use_id=tc.id,
								name=tc.name,
								content=text_search_result.model_dump(),
							)
							thread.messages.append(
								ChatMessage(
									role='tool',
									content=text_search_result.model_dump_json(),
									tool_call_id=tc.id,
									name=tc.name,
								)
							)
						elif tc.name == 'imageSearch':
							image_search_result = await self._rag_image.execute(paper_id, query)
							yield ToolResultEvent(
								tool_use_id=tc.id,
								name=tc.name,
								content=image_search_result.model_dump(),
							)
							thread.messages.append(
								ChatMessage(
									role='tool',
									content=image_search_result.model_dump_json(),
									tool_call_id=tc.id,
									name=tc.name,
								)
							)
						else:
							yield ErrorEvent(message=f'Unknown tool: {tc.name}')
							break

				# ループ内で最終テキストが得られなかった場合は tools なしで再度呼び出す
				if not accumulated:
					yield BlockStartEvent(index=block_index, block=TextBlock())
					user_indices = [i for i, m in enumerate(thread.messages) if m.role == 'user']
					cut_at = (
						user_indices[-MAX_CONVERSATION_TURNS]
						if len(user_indices) > MAX_CONVERSATION_TURNS
						else 0
					)
					context = thread.messages[cut_at:]
					async for chunk in self._llm.stream(context, [], SYSTEM_PROMPT):
						if isinstance(chunk, list):
							continue
						accumulated += chunk
						yield BlockDeltaEvent(index=block_index, delta=TextDelta(text=chunk))
					yield BlockStopEvent(index=block_index)

				thread.messages.append(ChatMessage(role='assistant', content=accumulated))

				thread.updated_at = datetime.now(UTC)
				await repo.update(thread)
		except Exception as e:
			self._logger.exception('Chat error for paper %s', paper_id)
			yield ErrorEvent(message=str(e))
			return

		yield MessageStopEvent()
