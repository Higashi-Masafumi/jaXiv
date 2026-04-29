"""migrate_chat_messages_to_content_blocks

旧形式（OpenAI 風 flat: role=user|assistant|tool, content=str, tool_calls, tool_call_id, name）
を Anthropic 互換の content-block 形式に変換する。

旧:
  user      : {role: 'user', content: str, ...}
  assistant : {role: 'assistant', content: str|null, tool_calls: [{id,name,args}]?, ...}
  tool      : {role: 'tool', content: '<json string>', tool_call_id, name, ...}

新:
  user      : {role: 'user', content: [{type:'text', text}]}
  assistant : {role: 'assistant', content: [
                  {type:'text', text}?,
                  {type:'tool_use', id, name, input}*
              ]}
  tool_resp : {role: 'user', content: [
                  {type:'tool_result', tool_use_id, name, content, is_error}*
              ]}

Revision ID: c2d4a7e9b1f3
Revises: 3b1e9f4d2a7c
Create Date: 2026-04-29 00:00:00.000000

"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any, Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'c2d4a7e9b1f3'
down_revision: Union[str, Sequence[str], None] = '3b1e9f4d2a7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now_iso() -> str:
	return datetime.now(UTC).isoformat()


def _new_id() -> str:
	return str(uuid.uuid4())


def _is_legacy(messages: list[dict[str, Any]]) -> bool:
	for m in messages:
		if m.get('role') == 'tool':
			return True
		content = m.get('content')
		if isinstance(content, str):
			return True
		if m.get('tool_calls') is not None:
			return True
	return False


def _legacy_to_blocks(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
	new_messages: list[dict[str, Any]] = []
	for m in messages:
		role = m.get('role')
		ts = m.get('timestamp') or _now_iso()
		mid = m.get('id') or _new_id()
		if role == 'user':
			text_value = m.get('content') or ''
			new_messages.append(
				{
					'id': mid,
					'role': 'user',
					'content': [{'type': 'text', 'text': text_value}],
					'timestamp': ts,
				}
			)
		elif role == 'assistant':
			blocks: list[dict[str, Any]] = []
			text_value = m.get('content')
			if text_value:
				blocks.append({'type': 'text', 'text': text_value})
			for tc in m.get('tool_calls') or []:
				blocks.append(
					{
						'type': 'tool_use',
						'id': tc.get('id') or _new_id(),
						'name': tc.get('name') or '',
						'input': tc.get('args') or {},
					}
				)
			if blocks:
				new_messages.append(
					{'id': mid, 'role': 'assistant', 'content': blocks, 'timestamp': ts}
				)
		elif role == 'tool':
			raw = m.get('content')
			if isinstance(raw, str):
				try:
					parsed = json.loads(raw)
				except (json.JSONDecodeError, TypeError):
					parsed = {'raw': raw}
			elif isinstance(raw, dict):
				parsed = raw
			else:
				parsed = {}
			block = {
				'type': 'tool_result',
				'tool_use_id': m.get('tool_call_id') or '',
				'name': m.get('name') or '',
				'content': parsed,
				'is_error': False,
			}
			# 直前が role='user' ですでに tool_result を持っているならそこに追加、
			# でなければ新しい user メッセージとして追加。
			if (
				new_messages
				and new_messages[-1]['role'] == 'user'
				and all(b.get('type') == 'tool_result' for b in new_messages[-1]['content'])
			):
				new_messages[-1]['content'].append(block)
			else:
				new_messages.append(
					{
						'id': mid,
						'role': 'user',
						'content': [block],
						'timestamp': ts,
					}
				)
	return new_messages


def upgrade() -> None:
	conn = op.get_bind()
	rows = conn.execute(text('SELECT id, messages FROM chat_thread')).fetchall()
	for row in rows:
		thread_id, messages = row
		if not messages:
			continue
		if not _is_legacy(messages):
			continue
		new_messages = _legacy_to_blocks(messages)
		conn.execute(
			text('UPDATE chat_thread SET messages = CAST(:m AS jsonb) WHERE id = :id'),
			{'m': json.dumps(new_messages), 'id': thread_id},
		)


def downgrade() -> None:
	# データのロスレス・ダウングレードは難しい（順序情報が新形式にだけ存在するため）。
	# 実運用ではこのマイグレーションは前進のみ想定。
	pass
