import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.repositories import IDigestDeliveryRepository
from domain.value_objects.user_id import UserId

from ..models import DigestDeliveryLogModel


class PostgresDigestDeliveryRepository(IDigestDeliveryRepository):
	"""Maps digest deliveries to the ``digest_delivery_log`` table."""

	def __init__(self, session: AsyncSession):
		self._session = session

	async def find_delivered_blog_ids(self, user_id: UserId) -> set[uuid.UUID]:
		stmt = select(col(DigestDeliveryLogModel.blog_post_id)).where(
			col(DigestDeliveryLogModel.user_id) == user_id.root
		)
		result = await self._session.execute(stmt)
		return {row[0] for row in result.all()}

	async def record_deliveries(self, user_id: UserId, blog_ids: list[uuid.UUID]) -> None:
		if not blog_ids:
			return
		now = datetime.now(UTC)
		rows = [
			{
				'id': uuid.uuid4(),
				'user_id': user_id.root,
				'blog_post_id': blog_id,
				'sent_at': now,
			}
			for blog_id in blog_ids
		]
		stmt = pg_insert(DigestDeliveryLogModel).values(rows)
		# Idempotent: skip pairs already recorded (unique on user_id + blog_post_id).
		stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'blog_post_id'])
		await self._session.execute(stmt)
