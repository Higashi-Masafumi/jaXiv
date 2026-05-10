from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl

from domain.value_objects.user_id import UserId


class CheckoutSession(BaseModel):
	model_config = ConfigDict(frozen=True)

	url: HttpUrl
	session_id: str


class PortalSession(BaseModel):
	model_config = ConfigDict(frozen=True)

	url: HttpUrl


class SubscriptionState(BaseModel):
	"""Subscription state extracted from a billing provider event."""

	model_config = ConfigDict(frozen=True)

	user_id: UserId
	stripe_customer_id: str
	stripe_subscription_id: str
	plan: Literal['free', 'paid']
	current_period_end: datetime | None
	cancel_at_period_end: bool


class SubscriptionUpdated(BaseModel):
	model_config = ConfigDict(frozen=True)

	state: SubscriptionState


class SubscriptionDeleted(BaseModel):
	model_config = ConfigDict(frozen=True)

	user_id: UserId


WebhookEffect = SubscriptionUpdated | SubscriptionDeleted


class IBillingGateway(ABC):
	"""Abstraction over the billing provider (Stripe)."""

	@abstractmethod
	async def create_checkout_session(
		self,
		*,
		user_id: UserId,
		stripe_customer_id: str | None,
	) -> CheckoutSession:
		"""Create a checkout session for a user."""
		raise NotImplementedError

	@abstractmethod
	async def create_portal_session(
		self,
		*,
		stripe_customer_id: str,
	) -> PortalSession:
		"""Create a portal session for a user."""
		raise NotImplementedError

	@abstractmethod
	async def resolve_webhook_event(
		self,
		*,
		payload: bytes,
		signature: str,
	) -> WebhookEffect | None:
		"""Parse a webhook event and return its domain-level effect, or None if unhandled."""
		raise NotImplementedError
