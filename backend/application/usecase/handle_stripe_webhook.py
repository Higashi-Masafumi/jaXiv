"""Apply a Stripe webhook event to the local subscription state."""

import uuid
from datetime import UTC, datetime
from logging import getLogger

from domain.entities.user_subscription import UserSubscription
from domain.gateways.i_billing_gateway import IBillingGateway, SubscriptionState
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.billing_account import BillingAccount
from domain.value_objects.user_id import UserId


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
		event = self._billing.parse_webhook_event(payload=payload, signature=signature)
		event_type = event.get('type', '')
		data_object = (event.get('data') or {}).get('object') or {}

		self._logger.info('Stripe webhook received: %s', event_type)

		if event_type == 'checkout.session.completed':
			subscription_id = data_object.get('subscription')
			if not subscription_id:
				self._logger.warning(
					'checkout.session.completed has no subscription id (event %s)',
					event.get('id'),
				)
				return
			state = await self._billing.fetch_subscription_state(str(subscription_id))
			if state is not None:
				await self._upsert_from_state(state)
			return

		if event_type in (
			'customer.subscription.created',
			'customer.subscription.updated',
		):
			subscription_id = data_object.get('id')
			if not subscription_id:
				return
			state = await self._billing.fetch_subscription_state(str(subscription_id))
			if state is not None:
				await self._upsert_from_state(state)
			return

		if event_type == 'customer.subscription.deleted':
			metadata = data_object.get('metadata') or {}
			user_id_str = metadata.get('user_id')
			if not user_id_str:
				self._logger.warning(
					'customer.subscription.deleted missing user_id metadata (event %s)',
					event.get('id'),
				)
				return
			await self._mark_free(user_id_str)
			return

		self._logger.debug('Stripe event type %s not handled', event_type)

	async def _upsert_from_state(self, state: SubscriptionState) -> None:
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

	async def _mark_free(self, user_id_str: str) -> None:
		try:
			parsed = UserId(uuid.UUID(user_id_str))
		except ValueError:
			self._logger.warning('Invalid user_id metadata in webhook: %s', user_id_str)
			return
		existing = await self._repo.find_by_user_id(parsed)
		# Keep the customer_id reference so the user can re-subscribe through
		# the same Stripe customer; clear subscription-level fields.
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
				user_id=parsed,
				plan='free',
				billing=billing,
				created_at=existing.created_at if existing else datetime.now(UTC),
			)
		)
