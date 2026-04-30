from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CheckoutSession:
	url: str
	session_id: str


@dataclass(frozen=True)
class PortalSession:
	url: str


@dataclass(frozen=True)
class SubscriptionState:
	"""Subscription state extracted from a Stripe webhook event."""

	user_id: str  # Supabase auth.users.id (uuid string)
	stripe_customer_id: str
	stripe_subscription_id: str
	plan: str  # 'free' | 'paid'
	current_period_end: datetime | None
	cancel_at_period_end: bool


class IBillingGateway(ABC):
	@abstractmethod
	async def create_checkout_session(
		self,
		*,
		user_id: str,
		customer_email: str | None,
		stripe_customer_id: str | None,
		success_url: str,
		cancel_url: str,
	) -> CheckoutSession: ...

	@abstractmethod
	async def create_portal_session(
		self,
		*,
		stripe_customer_id: str,
		return_url: str,
	) -> PortalSession: ...

	@abstractmethod
	def parse_webhook_event(
		self,
		*,
		payload: bytes,
		signature: str,
	) -> dict[str, Any]:
		"""Verify the Stripe signature and return the parsed event payload."""
		...

	@abstractmethod
	async def fetch_subscription_state(
		self, stripe_subscription_id: str
	) -> SubscriptionState | None:
		"""Fetch the latest state of a Stripe subscription by ID."""
		...
