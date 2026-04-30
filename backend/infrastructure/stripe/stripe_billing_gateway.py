"""Stripe-backed implementation of ``IBillingGateway``."""

from datetime import UTC, datetime
from logging import getLogger
from typing import Any

import stripe

from domain.gateways.i_billing_gateway import (
	CheckoutSession,
	IBillingGateway,
	PortalSession,
	SubscriptionState,
)

from .config import StripeConfig


def _to_datetime(epoch: int | None) -> datetime | None:
	if epoch is None:
		return None
	return datetime.fromtimestamp(epoch, tz=UTC)


def _plan_from_status(status: str | None) -> str:
	# Stripe statuses: 'active', 'trialing', 'past_due', 'canceled', etc.
	if status in ('active', 'trialing'):
		return 'paid'
	return 'free'


class StripeBillingGateway(IBillingGateway):
	def __init__(self, config: StripeConfig) -> None:
		self._config = config
		self._logger = getLogger(__name__)
		stripe.api_key = config.stripe_api_key

	async def create_checkout_session(
		self,
		*,
		user_id: str,
		customer_email: str | None,
		stripe_customer_id: str | None,
		success_url: str,
		cancel_url: str,
	) -> CheckoutSession:
		params: dict[str, Any] = {
			'mode': 'subscription',
			'line_items': [
				{'price': self._config.stripe_price_id_paid, 'quantity': 1},
			],
			'success_url': success_url,
			'cancel_url': cancel_url,
			'metadata': {'user_id': user_id},
			'subscription_data': {'metadata': {'user_id': user_id}},
			'client_reference_id': user_id,
		}
		if stripe_customer_id is not None:
			params['customer'] = stripe_customer_id
		elif customer_email is not None:
			params['customer_email'] = customer_email

		session = stripe.checkout.Session.create(**params)
		return CheckoutSession(url=session.url or '', session_id=session.id)

	async def create_portal_session(
		self,
		*,
		stripe_customer_id: str,
		return_url: str,
	) -> PortalSession:
		session = stripe.billing_portal.Session.create(
			customer=stripe_customer_id,
			return_url=return_url,
		)
		return PortalSession(url=session.url)

	def parse_webhook_event(
		self,
		*,
		payload: bytes,
		signature: str,
	) -> dict[str, Any]:
		event = stripe.Webhook.construct_event(
			payload=payload,
			sig_header=signature,
			secret=self._config.stripe_webhook_secret,
		)
		return dict(event)

	async def fetch_subscription_state(
		self, stripe_subscription_id: str
	) -> SubscriptionState | None:
		try:
			sub_obj = stripe.Subscription.retrieve(stripe_subscription_id)
		except stripe.StripeError:
			self._logger.exception('Failed to fetch Stripe subscription %s', stripe_subscription_id)
			return None

		# stripe.Subscription is dict-like via __getitem__/keys; convert to a
		# plain dict so mypy doesn't complain about typed attribute access.
		sub: dict[str, Any] = {k: sub_obj[k] for k in sub_obj.keys()}  # type: ignore[attr-defined]
		metadata = dict(sub.get('metadata') or {})
		user_id = metadata.get('user_id', '')
		if not user_id:
			self._logger.warning(
				'Stripe subscription %s has no user_id metadata; ignoring', sub.get('id')
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
