import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.chat import ChatThread
from domain.errors.domain_error import ChatThreadNotFoundError
from domain.repositories.i_chat_thread_repository import IChatThreadRepository
from domain.value_objects.user_id import UserId

from ..models import ChatThreadModel


class PostgresChatThreadRepository(IChatThreadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def find_by_id(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> ChatThread:
		result = await self._session.execute(
			select(ChatThreadModel).where(
				ChatThreadModel.id == thread_id,  # type: ignore[arg-type]
				ChatThreadModel.user_id == user_id,  # type: ignore[arg-type]
			)
		)
		row = result.scalar_one_or_none()
		if row is None:
			raise ChatThreadNotFoundError(str(thread_id))
		return ChatThread.model_validate(row.model_dump())

	async def update(self, thread: ChatThread) -> None:
		await self._session.execute(
			update(ChatThreadModel)
			.where(ChatThreadModel.id == thread.id)  # type: ignore[arg-type]
			.values(
				messages=[m.model_dump(mode='json') for m in thread.messages],
				updated_at=thread.updated_at,
			)
		)

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
		return ChatThread.model_validate(row.model_dump())

	async def find_by_paper_id(self, paper_id: str, user_id: uuid.UUID) -> list[ChatThread]:
		result = await self._session.execute(
			select(ChatThreadModel)
			.where(
				ChatThreadModel.paper_id == paper_id,  # type: ignore[arg-type]
				ChatThreadModel.user_id == user_id,  # type: ignore[arg-type]
			)
			.order_by(ChatThreadModel.updated_at.desc())  # type: ignore[attr-defined]
		)
		rows = result.scalars().all()
		return [ChatThread.model_validate(row.model_dump()) for row in rows]

	async def delete(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> None:
		result = await self._session.execute(
			delete(ChatThreadModel).where(
				ChatThreadModel.id == thread_id,  # type: ignore[arg-type]
				ChatThreadModel.user_id == user_id,  # type: ignore[arg-type]
			)
		)
		if result.rowcount == 0:
			raise ChatThreadNotFoundError(str(thread_id))

	async def count_user_messages(self, user_id: UserId, since: datetime) -> int:
		"""Count user-authored text messages from JSONB ``messages`` arrays.

		A "user-authored" message has ``role='user'`` and at least one
		``text`` content block (i.e. is not a synthetic tool_result message).
		"""
		stmt = text(
			"""
			SELECT count(*)
			FROM chat_thread t,
			     jsonb_array_elements(t.messages) m
			WHERE t.user_id = :user_id
			  AND m->>'role' = 'user'
			  AND (m->>'timestamp')::timestamptz >= :since
			  AND EXISTS (
			    SELECT 1
			    FROM jsonb_array_elements(m->'content') c
			    WHERE c->>'type' = 'text'
			  )
			"""
		)
		result = await self._session.execute(stmt, {'user_id': user_id.root, 'since': since})
		return int(result.scalar_one())
