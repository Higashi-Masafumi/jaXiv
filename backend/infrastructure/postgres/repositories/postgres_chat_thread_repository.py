import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.chat import ChatMessage, ChatThread, ToolCall
from domain.repositories.i_chat_thread_repository import IChatThreadRepository

from ..models import ChatThreadModel


class PostgresChatThreadRepository(IChatThreadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_entity(row: ChatThreadModel) -> ChatThread:
        messages = [
            ChatMessage(
                id=m['id'],
                role=m['role'],
                content=m.get('content'),
                tool_calls=[
                    ToolCall(id=tc['id'], name=tc['name'], args=tc['args'])
                    for tc in (m.get('tool_calls') or [])
                ] or None,
                tool_call_id=m.get('tool_call_id'),
                timestamp=datetime.fromisoformat(m['timestamp']),
            )
            for m in (row.messages or [])
        ]
        return ChatThread(
            id=row.id,
            paper_id=row.paper_id,
            user_id=row.user_id,
            messages=messages,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _messages_to_json(messages: list[ChatMessage]) -> list[dict]:
        result = []
        for m in messages:
            d: dict = {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'timestamp': m.timestamp.isoformat(),
            }
            if m.tool_calls:
                d['tool_calls'] = [
                    {'id': tc.id, 'name': tc.name, 'args': tc.args}
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                d['tool_call_id'] = m.tool_call_id
                d['name'] = m.role  # store tool name for context
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Repository methods
    # ------------------------------------------------------------------

    async def find_by_id(self, thread_id: uuid.UUID) -> ChatThread | None:
        result = await self._session.execute(
            select(ChatThreadModel).where(ChatThreadModel.id == thread_id)
        )
        row = result.scalar_one_or_none()
        return self._row_to_entity(row) if row else None

    async def find_by_id_and_user(
        self, thread_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatThread | None:
        result = await self._session.execute(
            select(ChatThreadModel).where(
                ChatThreadModel.id == thread_id,
                ChatThreadModel.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        return self._row_to_entity(row) if row else None

    async def save(self, thread: ChatThread) -> None:
        result = await self._session.execute(
            select(ChatThreadModel).where(ChatThreadModel.id == thread.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ChatThreadModel(
                id=thread.id,
                paper_id=thread.paper_id,
                user_id=thread.user_id,
                messages=self._messages_to_json(thread.messages),
                created_at=thread.created_at,
                updated_at=thread.updated_at,
            )
            self._session.add(row)
        else:
            row.messages = self._messages_to_json(thread.messages)
            row.updated_at = thread.updated_at
        await self._session.commit()

    async def create(self, paper_id: str, user_id: uuid.UUID) -> ChatThread:
        now = datetime.now(UTC)
        row = ChatThreadModel(
            paper_id=paper_id,
            user_id=user_id,
            messages=[],
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._row_to_entity(row)
