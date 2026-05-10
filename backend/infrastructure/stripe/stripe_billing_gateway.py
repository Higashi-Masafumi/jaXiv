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

# Stripe interpolates this literal token in the success_url at redirect time
# so the frontend can read the resulting Checkout session ID. Documented at
# https://stripe.com/docs/payments/checkout/custom-success-page
_STRIPE_SESSION_ID_TOKEN = '{CHECKOUT_SESSION_ID}'

# Subscription statuses Stripe considers "in good standing".
# https://stripe.com/docs/api/subscriptions/object#subscription_object-status
_ACTIVE_STRIPE_STATUSES = frozenset({'active', 'trialing'})


class StripeBillingGateway(IBillingGateway):
	def __init__(self, config: StripeConfig) -> None:
		self._config = config
		self._frontend_base_url = config.frontend_base_url.rstrip('/')
		self._logger = getLogger(__name__)
		stripe.api_key = config.stripe_api_key

	async def create_checkout_session(
		self,
		*,
		user_id: UserId,
		stripe_customer_id: str | None,
	) -> CheckoutSession:
		user_id_str = str(user_id.root)
		success_url = f'{self._frontend_base_url}/billing/success?session_id={_STRIPE_SESSION_ID_TOKEN}'
		params: dict[str, Any] = {
			'mode': 'subscription',
			'line_items': [
				{'price': self._config.stripe_price_id_paid, 'quantity': 1},
			],
			'success_url': success_url,
			'cancel_url': f'{self._frontend_base_url}/billing/cancel',
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
	) -> PortalSession:
		session = stripe.billing_portal.Session.create(
			customer=stripe_customer_id,
			return_url=f'{self._frontend_base_url}/pricing',
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
		# stripe.Webhook.construct_event already raises ValueError for malformed
		# payloads; let those propagate unchanged.
		return event.to_dict()

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
		metadata = sub_obj.metadata.to_dict()

		raw_user_id = metadata.get('user_id', '')
		if not raw_user_id:
			self._logger.warning(
				'Stripe subscription %s has no user_id metadata; ignoring',
				sub_obj.id,
			)
			return None
		try:
			user_id = UserId(uuid.UUID(raw_user_id))
		except ValueError:
			self._logger.warning(
				'Stripe subscription %s has invalid user_id metadata: %s',
				sub_obj.id,
				raw_user_id,
			)
			return None

		plan: Literal['free', 'paid'] = (
			'paid' if sub_obj.status in _ACTIVE_STRIPE_STATUSES else 'free'
		)
		current_period_end_epoch = sub_obj.current_period_end
		current_period_end = (
			datetime.fromtimestamp(current_period_end_epoch, tz=UTC)
			if current_period_end_epoch is not None
			else None
		)
		return SubscriptionState(
			user_id=user_id,
			stripe_customer_id=str(sub_obj.customer),
			stripe_subscription_id=str(sub_obj.id),
			plan=plan,
			current_period_end=current_period_end,
			cancel_at_period_end=bool(sub_obj.cancel_at_period_end),
		)
