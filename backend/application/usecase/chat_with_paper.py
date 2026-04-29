"""Agentic chat use case: routes user messages to Gemini with RAG tool support.

Anthropic Messages API 互換の content-block モデルで messages を扱う。
- assistant ターンは text と tool_use ブロックを **順序付きで** 1 メッセージにまとめる
- tool_result は **role='user'** メッセージの content に置く（Anthropic 形式）
"""

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
	MessageStartEvent,
	MessageStopEvent,
	TextDelta,
	ThreadIdEvent,
)
from application.unit_of_works.chat_thread_unit_of_work import ChatThreadUnitOfWork
from domain.entities.chat import (
	ChatMessage,
	ContentBlock,
	TextBlock,
	ToolResultBlock,
	ToolUseBlock,
)
from domain.gateways.i_chat_llm_gateway import (
	IChatLLMGateway,
	LLMTextDelta,
	LLMToolUse,
	ToolDefinition,
)

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


def _trim_context(messages: list[ChatMessage]) -> list[ChatMessage]:
	"""直近 MAX_CONVERSATION_TURNS 個の **テキストを含む** user メッセージから
	始まるコンテキストに絞る。tool_result だけが入った user メッセージは
	「ユーザーターン」ではないので、ターン予算には数えない。
	"""
	user_turn_indices = [
		i
		for i, m in enumerate(messages)
		if m.role == 'user' and any(isinstance(b, TextBlock) for b in m.content)
	]
	cut_at = (
		user_turn_indices[-MAX_CONVERSATION_TURNS]
		if len(user_turn_indices) > MAX_CONVERSATION_TURNS
		else 0
	)
	return messages[cut_at:]


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

	async def _run_tool(
		self, paper_id: str, tool_use: LLMToolUse
	) -> ToolResultBlock | None:
		query = tool_use.input.get('query', '')
		if tool_use.name == 'textSearch':
			text_result = await self._rag_text.execute(paper_id, query)
			return ToolResultBlock(
				tool_use_id=tool_use.id,
				name=tool_use.name,
				content=text_result.model_dump(),
			)
		if tool_use.name == 'imageSearch':
			image_result = await self._rag_image.execute(paper_id, query)
			return ToolResultBlock(
				tool_use_id=tool_use.id,
				name=tool_use.name,
				content=image_result.model_dump(),
			)
		return None

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

				user_message = ChatMessage(
					role='user', content=[TextBlock(text=message)]
				)
				thread.messages.append(user_message)

				block_index = 0
				final_text = ''

				for _ in range(MAX_TOOL_ROUNDS):
					assistant_id = str(uuid.uuid4())
					yield MessageStartEvent(message_id=assistant_id, role='assistant')

					iteration_text = ''
					tool_uses: list[LLMToolUse] = []
					assistant_blocks: list[ContentBlock] = []

					yield BlockStartEvent(index=block_index, block=TextBlock(text=''))
					context = _trim_context(thread.messages)
					async for event in self._llm.stream(context, RAG_TOOLS, SYSTEM_PROMPT):
						if isinstance(event, LLMTextDelta):
							iteration_text += event.text
							yield BlockDeltaEvent(
								index=block_index, delta=TextDelta(text=event.text)
							)
						elif isinstance(event, LLMToolUse):
							tool_uses.append(event)
					yield BlockStopEvent(index=block_index)
					block_index += 1

					if iteration_text:
						assistant_blocks.append(TextBlock(text=iteration_text))

					for tu in tool_uses:
						use_block = ToolUseBlock(id=tu.id, name=tu.name, input=tu.input)
						assistant_blocks.append(use_block)
						yield BlockStartEvent(index=block_index, block=use_block)
						yield BlockStopEvent(index=block_index)
						block_index += 1

					if assistant_blocks:
						thread.messages.append(
							ChatMessage(
								id=assistant_id, role='assistant', content=assistant_blocks
							)
						)

					if not tool_uses:
						final_text = iteration_text
						break

					tool_result_blocks: list[ContentBlock] = []
					tool_user_id = str(uuid.uuid4())
					yield MessageStartEvent(message_id=tool_user_id, role='user')
					unknown_tool = False
					for tu in tool_uses:
						result_block = await self._run_tool(paper_id, tu)
						if result_block is None:
							yield ErrorEvent(message=f'Unknown tool: {tu.name}')
							unknown_tool = True
							break
						tool_result_blocks.append(result_block)
						yield BlockStartEvent(index=block_index, block=result_block)
						yield BlockStopEvent(index=block_index)
						block_index += 1
					if tool_result_blocks:
						thread.messages.append(
							ChatMessage(
								id=tool_user_id, role='user', content=tool_result_blocks
							)
						)
					if unknown_tool:
						break

				# tool ループ内で最終 assistant テキストが得られなかった場合は
				# tools なしで最後にもう一度生成してまとめのテキストを返す
				if not final_text:
					assistant_id = str(uuid.uuid4())
					yield MessageStartEvent(message_id=assistant_id, role='assistant')
					yield BlockStartEvent(index=block_index, block=TextBlock(text=''))
					closing_text = ''
					context = _trim_context(thread.messages)
					async for event in self._llm.stream(context, [], SYSTEM_PROMPT):
						if isinstance(event, LLMTextDelta):
							closing_text += event.text
							yield BlockDeltaEvent(
								index=block_index, delta=TextDelta(text=event.text)
							)
					yield BlockStopEvent(index=block_index)
					block_index += 1
					if closing_text:
						thread.messages.append(
							ChatMessage(
								id=assistant_id,
								role='assistant',
								content=[TextBlock(text=closing_text)],
							)
						)

				thread.updated_at = datetime.now(UTC)
				await repo.update(thread)
		except Exception as e:
			self._logger.exception('Chat error for paper %s', paper_id)
			yield ErrorEvent(message=str(e))
			return

		yield MessageStopEvent()
