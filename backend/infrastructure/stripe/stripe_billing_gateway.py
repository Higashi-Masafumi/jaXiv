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
	SubscriptionDeleted,
	SubscriptionState,
	SubscriptionUpdated,
	WebhookEffect,
)
from domain.value_objects.user_id import UserId

from .config import StripeConfig


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
	) -> CheckoutSession:
		user_id_str = str(user_id.root)
		frontend = self._config.frontend_base_url
		params: dict[str, Any] = {
			'mode': 'subscription',
			'line_items': [
				{'price': self._config.stripe_price_id_paid, 'quantity': 1},
			],
			'success_url': f'{frontend}/billing/success?session_id={{CHECKOUT_SESSION_ID}}',
			'cancel_url': f'{frontend}/billing/cancel',
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
		frontend = self._config.frontend_base_url
		session = stripe.billing_portal.Session.create(
			customer=stripe_customer_id,
			return_url=f'{frontend}/pricing',
		)
		return PortalSession(url=HttpUrl(session.url))

	async def resolve_webhook_event(
		self,
		*,
		payload: bytes,
		signature: str,
	) -> WebhookEffect | None:
		try:
			event = stripe.Webhook.construct_event(
				payload=payload,
				sig_header=signature,
				secret=self._config.stripe_webhook_secret,
			)
		except stripe.SignatureVerificationError as e:
			raise ValueError(f'Invalid Stripe signature: {e}') from e

		event_type: str = event.type
		data_object = event.data.object

		if event_type in {
			'checkout.session.completed',
			'customer.subscription.created',
			'customer.subscription.updated',
		}:
			subscription_id = (
				data_object.subscription
				if event_type == 'checkout.session.completed'
				else data_object.id
			)
			if not subscription_id:
				self._logger.warning(
					'%s has no subscription id (event %s)',
					event_type,
					event.id,
				)
				return None
			return self._resolve_subscription_updated(str(subscription_id))

		if event_type == 'customer.subscription.deleted':
			raw_user_id = (data_object.metadata or {}).get('user_id', '')
			if not raw_user_id:
				self._logger.warning(
					'customer.subscription.deleted missing user_id metadata (event %s)',
					event.id,
				)
				return None
			try:
				return SubscriptionDeleted(user_id=UserId(uuid.UUID(raw_user_id)))
			except ValueError:
				self._logger.warning('Invalid user_id metadata: %s', raw_user_id)
				return None

		self._logger.debug('Stripe event type %s not handled', event_type)
		return None

	def _resolve_subscription_updated(
		self,
		subscription_id: str,
	) -> SubscriptionUpdated | None:
		try:
			sub = stripe.Subscription.retrieve(subscription_id)
		except stripe.StripeError:
			self._logger.exception('Failed to fetch Stripe subscription %s', subscription_id)
			return None

		raw_user_id = (sub.metadata or {}).get('user_id', '')
		if not raw_user_id:
			self._logger.warning('Subscription %s has no user_id metadata', sub.id)
			return None
		try:
			user_id = UserId(uuid.UUID(raw_user_id))
		except ValueError:
			self._logger.warning('Subscription %s has invalid user_id: %s', sub.id, raw_user_id)
			return None

		plan: Literal['free', 'paid'] = 'paid' if sub.status in {'active', 'trialing'} else 'free'
		current_period_end = (
			datetime.fromtimestamp(sub.current_period_end, tz=UTC)
			if sub.current_period_end is not None
			else None
		)
		return SubscriptionUpdated(
			state=SubscriptionState(
				user_id=user_id,
				stripe_customer_id=str(sub.customer),
				stripe_subscription_id=str(sub.id),
				plan=plan,
				current_period_end=current_period_end,
				cancel_at_period_end=bool(sub.cancel_at_period_end),
			),
		)
