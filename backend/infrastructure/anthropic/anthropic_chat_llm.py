"""Anthropic (Claude) implementation of the chat LLM gateway.

ドメイン層はもともと Anthropic Messages API 互換の content-block モデルで設計
されているため、変換は素直に 1:1 で行える。

コスト最適化として **プロンプトキャッシュ**（``cache_control: ephemeral``）を使う。
1 回のユーザー発話に対して tool ループで最大 ``MAX_TOOL_ROUNDS`` 回 LLM を呼び、
そのたびに増え続ける会話履歴を再送する。直近メッセージの末尾ブロックに
ブレークポイントを置くことで、system + tools + これまでの履歴という共通プレフィクス
がラウンド間でキャッシュ読み出し（フル価格の ~0.1 倍）になる。
"""

import json
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from anthropic import NOT_GIVEN, AsyncAnthropic, AsyncAnthropicVertex

from domain.entities.chat import ChatMessage, TextBlock, ToolResultBlock, ToolUseBlock
from domain.gateways.i_chat_llm_gateway import (
	IChatLLMGateway,
	LLMStreamEvent,
	LLMTextDelta,
	LLMToolUse,
	ToolDefinition,
)
from infrastructure.anthropic.config import get_anthropic_config

_CACHE_CONTROL: dict[str, str] = {'type': 'ephemeral'}


class AnthropicChatLLM(IChatLLMGateway):
	# ストリーミングなので HTTP タイムアウトの懸念はない。RAG 回答が途中で
	# 切れないよう十分な上限を取りつつ、暴走を防ぐ範囲に収める。
	MAX_TOKENS = 8192

	def __init__(self, model: str | None = None) -> None:
		config = get_anthropic_config()
		self._client: AsyncAnthropic | AsyncAnthropicVertex
		if config.anthropic_provider == 'vertex':
			# 認証は GCP ADC。project_id 未指定なら環境（GOOGLE_CLOUD_PROJECT/ADC）から解決。
			self._client = AsyncAnthropicVertex(
				project_id=config.gcp_project_id or NOT_GIVEN,
				region=config.vertex_region,
			)
		else:
			self._client = AsyncAnthropic(api_key=config.anthropic_api_key.get_secret_value())
		self._model = model or config.anthropic_chat_model
		self._logger = getLogger(__name__)

	def _to_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
		"""ContentBlock ベースのメッセージを Anthropic の messages 配列へ変換する。

		- assistant の text/tool_use はそのまま content ブロックへ
		- user の text/tool_result も content ブロックへ（tool_result content は
		  ドメインでは dict なので JSON 文字列にして渡す）
		"""
		out: list[dict[str, Any]] = []
		for msg in messages:
			content: list[dict[str, Any]] = []
			for block in msg.content:
				if isinstance(block, TextBlock):
					if block.text:
						content.append({'type': 'text', 'text': block.text})
				elif isinstance(block, ToolUseBlock):
					content.append(
						{
							'type': 'tool_use',
							'id': block.id,
							'name': block.name,
							'input': block.input,
						}
					)
				elif isinstance(block, ToolResultBlock):
					content.append(
						{
							'type': 'tool_result',
							'tool_use_id': block.tool_use_id,
							'content': json.dumps(block.content, ensure_ascii=False),
							'is_error': block.is_error,
						}
					)
			if content:
				out.append({'role': msg.role, 'content': content})
		# 直近メッセージ末尾にキャッシュブレークポイントを置き、tool ループの
		# 各ラウンドで共通プレフィクス（system + tools + 履歴）を再利用する。
		if out:
			out[-1]['content'][-1]['cache_control'] = _CACHE_CONTROL
		return out

	async def stream(
		self,
		messages: list[ChatMessage],
		tools: list[ToolDefinition],
		system_prompt: str,
	) -> AsyncIterator[LLMStreamEvent]:
		kwargs: dict[str, Any] = {
			'model': self._model,
			'max_tokens': self.MAX_TOKENS,
			'system': [{'type': 'text', 'text': system_prompt, 'cache_control': _CACHE_CONTROL}],
			'messages': self._to_messages(messages),
		}
		if tools:
			kwargs['tools'] = [
				{'name': t.name, 'description': t.description, 'input_schema': t.parameters}
				for t in tools
			]

		# index -> 組み立て中の tool_use ブロック（input は partial_json を連結して復元）
		tool_blocks: dict[int, dict[str, str]] = {}

		async with self._client.messages.stream(**kwargs) as stream:
			async for event in stream:
				if event.type == 'content_block_start':
					block = event.content_block
					if block.type == 'tool_use':
						tool_blocks[event.index] = {'id': block.id, 'name': block.name, 'buf': ''}
				elif event.type == 'content_block_delta':
					delta = event.delta
					if delta.type == 'text_delta':
						yield LLMTextDelta(text=delta.text)
					elif delta.type == 'input_json_delta':
						tb = tool_blocks.get(event.index)
						if tb is not None:
							tb['buf'] += delta.partial_json
				elif event.type == 'content_block_stop':
					tb = tool_blocks.pop(event.index, None)
					if tb is not None:
						raw = tb['buf'].strip()
						try:
							parsed = json.loads(raw) if raw else {}
						except json.JSONDecodeError:
							self._logger.warning('Failed to parse tool input JSON: %r', raw)
							parsed = {}
						yield LLMToolUse(id=tb['id'], name=tb['name'], input=parsed)
