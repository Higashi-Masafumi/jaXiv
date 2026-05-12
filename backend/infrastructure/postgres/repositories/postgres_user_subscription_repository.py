from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.user_subscription import UserSubscription
from domain.repositories import IUserSubscriptionRepository
from domain.value_objects.billing_account import BillingAccount
from domain.value_objects.subscription_plan import SubscriptionPlan
from domain.value_objects.user_id import UserId

from ..models import UserSubscriptionModel


class PostgresUserSubscriptionRepository(IUserSubscriptionRepository):
	"""Maps ``UserSubscription`` to the ``user_subscription`` table.

	The table still stores Stripe-specific column names (``stripe_*``) since
	Stripe is the only provider we currently use. The mapping here translates
	those columns into the provider-agnostic ``BillingAccount`` value
	object on the domain side.
	"""

	def __init__(self, session: AsyncSession):
		self._session = session
		self._logger = getLogger(__name__)

	def _to_entity(self, row: UserSubscriptionModel) -> UserSubscription:
		billing: BillingAccount | None = None
		if row.stripe_customer_id is not None:
			billing = BillingAccount(
				customer_id=row.stripe_customer_id,
				subscription_id=row.stripe_subscription_id,
				current_period_end=row.current_period_end,
				cancel_at_period_end=row.cancel_at_period_end,
			)
		return UserSubscription(
			user_id=UserId(row.user_id),
			plan=SubscriptionPlan(row.plan),
			billing=billing,
			created_at=row.created_at,
			updated_at=row.updated_at,
		)

	async def find_by_user_id(self, user_id: UserId) -> UserSubscription | None:
		stmt = select(UserSubscriptionModel).where(
			col(UserSubscriptionModel.user_id) == user_id.root
		)
		result = await self._session.execute(stmt)
		row = result.scalars().first()
		return self._to_entity(row) if row is not None else None

	async def upsert(self, subscription: UserSubscription) -> UserSubscription:
		now = datetime.now(UTC)
		billing = subscription.billing
		values = {
			'user_id': subscription.user_id.root,
			'plan': subscription.plan.value,
			'stripe_customer_id': billing.customer_id if billing else None,
			'stripe_subscription_id': billing.subscription_id if billing else None,
			'current_period_end': billing.current_period_end if billing else None,
			'cancel_at_period_end': billing.cancel_at_period_end if billing else False,
			'created_at': subscription.created_at or now,
			'updated_at': now,
		}
		stmt = pg_insert(UserSubscriptionModel).values(**values)
		stmt = stmt.on_conflict_do_update(
			index_elements=['user_id'],
			set_={
				'plan': stmt.excluded.plan,
				'stripe_customer_id': stmt.excluded.stripe_customer_id,
				'stripe_subscription_id': stmt.excluded.stripe_subscription_id,
				'current_period_end': stmt.excluded.current_period_end,
				'cancel_at_period_end': stmt.excluded.cancel_at_period_end,
				'updated_at': stmt.excluded.updated_at,
			},
		)
		await self._session.execute(stmt)

		refreshed = await self.find_by_user_id(subscription.user_id)
		assert refreshed is not None
		return refreshed
