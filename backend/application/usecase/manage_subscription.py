"""Use cases for subscription management via Stripe."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from logging import getLogger

from domain.entities.auth_user import AuthUser
from domain.entities.user_subscription import UserSubscription
from domain.gateways.i_billing_gateway import (
	CheckoutSession,
	IBillingGateway,
	PortalSession,
	SubscriptionState,
)
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.user_id import UserId


@dataclass(frozen=True)
class MySubscriptionView:
	plan: str  # 'free' | 'paid'
	current_period_end: datetime | None
	cancel_at_period_end: bool
	has_stripe_customer: bool


class GetMySubscriptionUseCase:
	def __init__(self, repo: IUserSubscriptionRepository) -> None:
		self._repo = repo

	async def execute(self, auth_user: AuthUser) -> MySubscriptionView:
		sub = await self._repo.find_by_user_id(auth_user.user_id)
		if sub is None:
			return MySubscriptionView(
				plan='free',
				current_period_end=None,
				cancel_at_period_end=False,
				has_stripe_customer=False,
			)
		return MySubscriptionView(
			plan=sub.plan,
			current_period_end=sub.current_period_end,
			cancel_at_period_end=sub.cancel_at_period_end,
			has_stripe_customer=sub.stripe_customer_id is not None,
		)


class StartCheckoutUseCase:
	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
	) -> None:
		self._billing = billing
		self._repo = repo

	async def execute(
		self,
		*,
		auth_user: AuthUser,
		customer_email: str | None,
		success_url: str,
		cancel_url: str,
	) -> CheckoutSession:
		existing = await self._repo.find_by_user_id(auth_user.user_id)
		stripe_customer_id = existing.stripe_customer_id if existing else None
		return await self._billing.create_checkout_session(
			user_id=str(auth_user.user_id.root),
			customer_email=customer_email,
			stripe_customer_id=stripe_customer_id,
			success_url=success_url,
			cancel_url=cancel_url,
		)


class StartCustomerPortalUseCase:
	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
	) -> None:
		self._billing = billing
		self._repo = repo

	async def execute(
		self, *, auth_user: AuthUser, return_url: str
	) -> PortalSession | None:
		sub = await self._repo.find_by_user_id(auth_user.user_id)
		if sub is None or sub.stripe_customer_id is None:
			return None
		return await self._billing.create_portal_session(
			stripe_customer_id=sub.stripe_customer_id,
			return_url=return_url,
		)


class HandleStripeWebhookUseCase:
	"""Apply a Stripe webhook event to the local subscription state."""

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
			user_id = (
				data_object.get('client_reference_id')
				or (data_object.get('metadata') or {}).get('user_id')
			)
			subscription_id = data_object.get('subscription')
			customer_id = data_object.get('customer')
			if not user_id or not subscription_id or not customer_id:
				self._logger.warning(
					'checkout.session.completed missing fields; ignoring (event %s)',
					event.get('id'),
				)
				return
			state = await self._billing.fetch_subscription_state(str(subscription_id))
			if state is None:
				return
			await self._upsert_from_state(uuid.UUID(user_id), state)
			return

		if event_type in (
			'customer.subscription.created',
			'customer.subscription.updated',
			'customer.subscription.deleted',
		):
			subscription_id = data_object.get('id')
			metadata = data_object.get('metadata') or {}
			user_id_str = metadata.get('user_id')
			if not subscription_id or not user_id_str:
				self._logger.warning(
					'%s missing user_id metadata; ignoring (event %s)',
					event_type,
					event.get('id'),
				)
				return

			if event_type == 'customer.subscription.deleted':
				existing = await self._repo.find_by_user_id(UserId(uuid.UUID(user_id_str)))
				updated = UserSubscription(
					user_id=UserId(uuid.UUID(user_id_str)),
					plan='free',
					stripe_customer_id=existing.stripe_customer_id if existing else None,
					stripe_subscription_id=None,
					current_period_end=None,
					cancel_at_period_end=False,
					created_at=existing.created_at if existing else datetime.now(UTC),
				)
				await self._repo.upsert(updated)
				return

			state = await self._billing.fetch_subscription_state(str(subscription_id))
			if state is None:
				return
			await self._upsert_from_state(uuid.UUID(user_id_str), state)
			return

		self._logger.debug('Stripe event type %s not handled', event_type)

	async def _upsert_from_state(
		self, user_id: uuid.UUID, state: SubscriptionState
	) -> None:
		existing = await self._repo.find_by_user_id(UserId(user_id))
		plan: str = state.plan if state.plan in ('free', 'paid') else 'free'
		await self._repo.upsert(
			UserSubscription(
				user_id=UserId(user_id),
				plan=plan,  # type: ignore[arg-type]
				stripe_customer_id=state.stripe_customer_id,
				stripe_subscription_id=state.stripe_subscription_id,
				current_period_end=state.current_period_end,
				cancel_at_period_end=state.cancel_at_period_end,
				created_at=existing.created_at if existing else datetime.now(UTC),
			)
		)
