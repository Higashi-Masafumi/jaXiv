"""Stripe-backed implementation of ``IBillingGateway``."""

import uuid
from datetime import UTC, datetime
from logging import getLogger
from typing import Any, Literal

import stripe
from pydantic import HttpUrl

from domain.gateways.i_billing_gateway import (
	CheckoutSession,
	IBillingGateway,
	PortalSession,
	SubscriptionState,
)
from domain.value_objects.user_id import UserId

from .config import StripeConfig

# Stripe-only token: tells Checkout to interpolate the session ID into the URL.
_STRIPE_SESSION_ID_TOKEN = '{CHECKOUT_SESSION_ID}'


def _to_datetime(epoch: int | None) -> datetime | None:
	if epoch is None:
		return None
	return datetime.fromtimestamp(epoch, tz=UTC)


def _plan_from_status(status: str | None) -> Literal['free', 'paid']:
	# Stripe statuses: 'active', 'trialing', 'past_due', 'canceled', etc.
	if status in ('active', 'trialing'):
		return 'paid'
	return 'free'


def _with_session_id_token(success_url: HttpUrl) -> str:
	"""Append Stripe's ``{CHECKOUT_SESSION_ID}`` interpolation token.

	Stripe Checkout requires the ``success_url`` to embed the literal token
	``{CHECKOUT_SESSION_ID}``; Stripe substitutes the actual session ID at
	redirect time so the frontend can identify which checkout completed.
	The token is Stripe-specific, so building it lives here rather than in
	the application layer.
	"""
	url = str(success_url)
	separator = '&' if '?' in url else '?'
	return f'{url}{separator}session_id={_STRIPE_SESSION_ID_TOKEN}'


class StripeBillingGateway(IBillingGateway):
	def __init__(self, config: StripeConfig) -> None:
		self._config = config
		self._logger = getLogger(__name__)
		stripe.api_key = config.stripe_api_key

	async def create_checkout_session(
		self,
		*,
		user_id: UserId,
		stripe_customer_id: str | None,
		success_url: HttpUrl,
		cancel_url: HttpUrl,
	) -> CheckoutSession:
		user_id_str = str(user_id.root)
		params: dict[str, Any] = {
			'mode': 'subscription',
			'line_items': [
				{'price': self._config.stripe_price_id_paid, 'quantity': 1},
			],
			'success_url': _with_session_id_token(success_url),
			'cancel_url': str(cancel_url),
			'metadata': {'user_id': user_id_str},
			'subscription_data': {'metadata': {'user_id': user_id_str}},
			'client_reference_id': user_id_str,
		}
		if stripe_customer_id is not None:
			params['customer'] = stripe_customer_id

		session = stripe.checkout.Session.create(**params)
		return CheckoutSession(
			url=HttpUrl(session.url or ''),
			session_id=session.id,
		)

	async def create_portal_session(
		self,
		*,
		stripe_customer_id: str,
		return_url: HttpUrl,
	) -> PortalSession:
		session = stripe.billing_portal.Session.create(
			customer=stripe_customer_id,
			return_url=str(return_url),
		)
		return PortalSession(url=HttpUrl(session.url))

	def parse_webhook_event(
		self,
		*,
		payload: bytes,
		signature: str,
	) -> dict[str, Any]:
		try:
			event = stripe.Webhook.construct_event(
				payload=payload,
				sig_header=signature,
				secret=self._config.stripe_webhook_secret,
			)
		except stripe.SignatureVerificationError as e:
			# Re-raise as ValueError so the controller maps it to 400 without
			# leaking the Stripe SDK error type into the application layer.
			raise ValueError(f'Invalid Stripe signature: {e}') from e
		except ValueError:
			# stripe.Webhook.construct_event already raises ValueError for
			# malformed payloads; let it propagate unchanged.
			raise
		return dict(event)

	async def fetch_subscription_state(
		self, stripe_subscription_id: str
	) -> SubscriptionState | None:
		try:
			sub_obj = stripe.Subscription.retrieve(stripe_subscription_id)
		except stripe.StripeError:
			self._logger.exception(
				'Failed to fetch Stripe subscription %s', stripe_subscription_id
			)
			return None

		# stripe.Subscription is dict-like via __getitem__/keys; convert to a
		# plain dict so mypy doesn't complain about typed attribute access.
		sub: dict[str, Any] = {k: sub_obj[k] for k in sub_obj.keys()}  # type: ignore[attr-defined]
		metadata = dict(sub.get('metadata') or {})
		raw_user_id = metadata.get('user_id', '')
		if not raw_user_id:
			self._logger.warning(
				'Stripe subscription %s has no user_id metadata; ignoring',
				sub.get('id'),
			)
			return None
		try:
			user_id = UserId(uuid.UUID(raw_user_id))
		except ValueError:
			self._logger.warning(
				'Stripe subscription %s has invalid user_id metadata: %s',
				sub.get('id'),
				raw_user_id,
			)
			return None
		return SubscriptionState(
			user_id=user_id,
			stripe_customer_id=str(sub.get('customer')),
			stripe_subscription_id=str(sub.get('id')),
			plan=_plan_from_status(sub.get('status')),
			current_period_end=_to_datetime(sub.get('current_period_end')),
			cancel_at_period_end=bool(sub.get('cancel_at_period_end')),
		)
