"""Apply a Stripe webhook event to the local subscription state."""

from datetime import UTC, datetime
from logging import getLogger

from domain.entities.user_subscription import UserSubscription
from domain.gateways.i_billing_gateway import (
	IBillingGateway,
	SubscriptionDeleted,
	SubscriptionUpdated,
)
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.billing_account import BillingAccount


class HandleStripeWebhookUseCase:
	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
	) -> None:
		self._billing = billing
		self._repo = repo
		self._logger = getLogger(__name__)

	async def execute(self, *, payload: bytes, signature: str) -> None:
		effect = await self._billing.resolve_webhook_event(
			payload=payload,
			signature=signature,
		)
		if effect is None:
			return

		if isinstance(effect, SubscriptionUpdated):
			state = effect.state
			existing = await self._repo.find_by_user_id(state.user_id)
			await self._repo.upsert(
				UserSubscription(
					user_id=state.user_id,
					plan=state.plan,
					billing=BillingAccount(
						customer_id=state.stripe_customer_id,
						subscription_id=state.stripe_subscription_id,
						current_period_end=state.current_period_end,
						cancel_at_period_end=state.cancel_at_period_end,
					),
					created_at=existing.created_at if existing else datetime.now(UTC),
				)
			)
			return

		if isinstance(effect, SubscriptionDeleted):
			existing = await self._repo.find_by_user_id(effect.user_id)
			billing: BillingAccount | None = None
			if existing and existing.billing is not None:
				billing = BillingAccount(
					customer_id=existing.billing.customer_id,
					subscription_id=None,
					current_period_end=None,
					cancel_at_period_end=False,
				)
			await self._repo.upsert(
				UserSubscription(
					user_id=effect.user_id,
					plan='free',
					billing=billing,
					created_at=existing.created_at if existing else datetime.now(UTC),
				)
			)
