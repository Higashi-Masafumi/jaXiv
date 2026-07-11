from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.topic_subscription import TopicSubscription
from domain.repositories import ITopicSubscriptionRepository
from domain.value_objects.user_id import UserId

from ..models import UserTopicSubscriptionModel


class PostgresTopicSubscriptionRepository(ITopicSubscriptionRepository):
	"""Maps ``TopicSubscription`` to the ``user_topic_subscription`` table."""

	def __init__(self, session: AsyncSession):
		self._session = session
		self._logger = getLogger(__name__)

	def _to_entity(self, row: UserTopicSubscriptionModel) -> TopicSubscription:
		return TopicSubscription(
			id=row.id,
			user_id=UserId(row.user_id),
			keywords=row.keywords or [],
			is_active=row.is_active,
			created_at=row.created_at,
			updated_at=row.updated_at,
		)

	async def find_by_user_id(self, user_id: UserId) -> TopicSubscription | None:
		stmt = select(UserTopicSubscriptionModel).where(
			col(UserTopicSubscriptionModel.user_id) == user_id.root
		)
		result = await self._session.execute(stmt)
		# user_id is unique, so there is at most one row.
		row = result.scalars().one_or_none()
		return self._to_entity(row) if row is not None else None

	async def upsert(self, subscription: TopicSubscription) -> TopicSubscription:
		now = datetime.now(UTC)
		values = {
			'id': subscription.id,
			'user_id': subscription.user_id.root,
			'keywords': subscription.keywords,
			'is_active': subscription.is_active,
			'created_at': now,
			'updated_at': now,
		}
		stmt = pg_insert(UserTopicSubscriptionModel).values(**values)
		# On conflict, preserve id/created_at and only refresh the mutable fields.
		stmt = stmt.on_conflict_do_update(
			index_elements=['user_id'],
			set_={
				'keywords': stmt.excluded.keywords,
				'is_active': stmt.excluded.is_active,
				'updated_at': stmt.excluded.updated_at,
			},
		)
		result = await self._session.execute(stmt.returning(UserTopicSubscriptionModel))
		row = result.scalars().one()
		return self._to_entity(row)
