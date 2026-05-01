"""Use cases for subscription management via the billing gateway."""

from datetime import UTC, datetime
from logging import getLogger

from pydantic import BaseModel, ConfigDict

from domain.entities.auth_user import AuthUser
from domain.entities.user_subscription import UserSubscription
from domain.errors._base import DomainNotFoundError
from domain.gateways.i_billing_gateway import (
	CheckoutSession,
	IBillingGateway,
	PortalSession,
	SubscriptionState,
)
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.frontend_urls import FrontendUrls
from domain.value_objects.user_id import UserId


class MySubscriptionView(BaseModel):
	model_config = ConfigDict(frozen=True)

	plan: str  # 'free' | 'paid'
	current_period_end: datetime | None
	cancel_at_period_end: bool
	has_billing_account: bool


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
				has_billing_account=False,
			)
		return MySubscriptionView(
			plan=sub.plan,
			current_period_end=sub.current_period_end,
			cancel_at_period_end=sub.cancel_at_period_end,
			has_billing_account=sub.stripe_customer_id is not None,
		)


class StartCheckoutUseCase:
	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
		urls: FrontendUrls,
	) -> None:
		self._billing = billing
		self._repo = repo
		self._urls = urls

	async def execute(self, *, auth_user: AuthUser) -> CheckoutSession:
		existing = await self._repo.find_by_user_id(auth_user.user_id)
		stripe_customer_id = existing.stripe_customer_id if existing else None
		return await self._billing.create_checkout_session(
			user_id=auth_user.user_id,
			stripe_customer_id=stripe_customer_id,
			success_url=self._urls.billing_success,
			cancel_url=self._urls.billing_cancel,
		)


class NoBillingAccountError(DomainNotFoundError):
	"""Raised when a user has no billing-provider customer record yet."""

	def __init__(self, user_id: UserId) -> None:
		super().__init__(f'No billing account for user {user_id.root}')
		self.user_id = user_id


class StartCustomerPortalUseCase:
	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
		urls: FrontendUrls,
	) -> None:
		self._billing = billing
		self._repo = repo
		self._urls = urls

	async def execute(self, *, auth_user: AuthUser) -> PortalSession:
		sub = await self._repo.find_by_user_id(auth_user.user_id)
		if sub is None or sub.stripe_customer_id is None:
			raise NoBillingAccountError(auth_user.user_id)
		return await self._billing.create_portal_session(
			stripe_customer_id=sub.stripe_customer_id,
			return_url=self._urls.pricing,
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
				stripe_customer_id=state.stripe_customer_id,
				stripe_subscription_id=state.stripe_subscription_id,
				current_period_end=state.current_period_end,
				cancel_at_period_end=state.cancel_at_period_end,
				created_at=existing.created_at if existing else datetime.now(UTC),
			)
		)

	async def _mark_free(self, user_id_str: str) -> None:
		import uuid

		try:
			parsed = UserId(uuid.UUID(user_id_str))
		except ValueError:
			self._logger.warning('Invalid user_id metadata in webhook: %s', user_id_str)
			return
		existing = await self._repo.find_by_user_id(parsed)
		await self._repo.upsert(
			UserSubscription(
				user_id=parsed,
				plan='free',
				stripe_customer_id=existing.stripe_customer_id if existing else None,
				stripe_subscription_id=None,
				current_period_end=None,
				cancel_at_period_end=False,
				created_at=existing.created_at if existing else datetime.now(UTC),
			)
		)
