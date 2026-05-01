from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Literal

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


class IBillingGateway(ABC):
	"""Abstraction over the billing provider (Stripe).

	The gateway is the only layer that knows how to talk to Stripe. Use cases
	pass plain page URLs (where the user should land after Checkout) and the
	gateway internally adapts them to provider-specific formats (e.g. the
	``{CHECKOUT_SESSION_ID}`` placeholder Stripe expects).
	"""

	@abstractmethod
	async def create_checkout_session(
		self,
		*,
		user_id: UserId,
		stripe_customer_id: str | None,
		success_url: HttpUrl,
		cancel_url: HttpUrl,
	) -> CheckoutSession: ...

	@abstractmethod
	async def create_portal_session(
		self,
		*,
		stripe_customer_id: str,
		return_url: HttpUrl,
	) -> PortalSession: ...

	@abstractmethod
	def parse_webhook_event(
		self,
		*,
		payload: bytes,
		signature: str,
	) -> dict[str, Any]:
		"""Verify the provider signature and return the parsed event payload."""
		...

	@abstractmethod
	async def fetch_subscription_state(
		self, stripe_subscription_id: str
	) -> SubscriptionState | None:
		"""Fetch the latest state of a subscription by ID."""
		...
