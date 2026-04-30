from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from application.usecase import (
	GetMySubscriptionUseCase,
	HandleStripeWebhookUseCase,
	MySubscriptionView,
	StartCheckoutUseCase,
	StartCustomerPortalUseCase,
)
from domain.entities.auth_user import AuthUser
from infrastructure.dependencies import (
	get_get_my_subscription_use_case,
	get_handle_stripe_webhook_use_case,
	get_required_auth_user,
	get_start_checkout_use_case,
	get_start_customer_portal_use_case,
)
from infrastructure.stripe.config import StripeConfig, get_stripe_config

router = APIRouter(prefix='/api/v1/billing')


class MySubscriptionResponse(BaseModel):
	plan: str
	current_period_end: str | None
	cancel_at_period_end: bool
	has_stripe_customer: bool

	@classmethod
	def from_view(cls, view: MySubscriptionView) -> 'MySubscriptionResponse':
		return cls(
			plan=view.plan,
			current_period_end=view.current_period_end.isoformat()
			if view.current_period_end
			else None,
			cancel_at_period_end=view.cancel_at_period_end,
			has_stripe_customer=view.has_stripe_customer,
		)


class CheckoutSessionResponse(BaseModel):
	url: str


@router.get('/me', response_model=MySubscriptionResponse)
async def get_my_subscription(
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[GetMySubscriptionUseCase, Depends(get_get_my_subscription_use_case)],
) -> MySubscriptionResponse:
	view = await use_case.execute(auth_user=auth_user)
	return MySubscriptionResponse.from_view(view)


@router.post('/checkout-session', response_model=CheckoutSessionResponse)
async def create_checkout_session(
	request: Request,
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[StartCheckoutUseCase, Depends(get_start_checkout_use_case)],
	config: Annotated[StripeConfig, Depends(get_stripe_config)],
) -> CheckoutSessionResponse:
	base = config.frontend_base_url.rstrip('/')
	customer_email = request.headers.get('x-user-email')
	session = await use_case.execute(
		auth_user=auth_user,
		customer_email=customer_email,
		success_url=f'{base}/billing/success?session_id={{CHECKOUT_SESSION_ID}}',
		cancel_url=f'{base}/billing/cancel',
	)
	return CheckoutSessionResponse(url=session.url)


@router.post('/portal-session', response_model=CheckoutSessionResponse)
async def create_portal_session(
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[
		StartCustomerPortalUseCase, Depends(get_start_customer_portal_use_case)
	],
	config: Annotated[StripeConfig, Depends(get_stripe_config)],
) -> CheckoutSessionResponse:
	base = config.frontend_base_url.rstrip('/')
	session = await use_case.execute(auth_user=auth_user, return_url=f'{base}/pricing')
	if session is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail='No Stripe customer found for this user.',
		)
	return CheckoutSessionResponse(url=session.url)


@router.post('/webhook', status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
	request: Request,
	use_case: Annotated[
		HandleStripeWebhookUseCase, Depends(get_handle_stripe_webhook_use_case)
	],
	stripe_signature: Annotated[str | None, Header(alias='stripe-signature')] = None,
) -> None:
	if stripe_signature is None:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail='Missing Stripe signature header.',
		)
	payload = await request.body()
	try:
		await use_case.execute(payload=payload, signature=stripe_signature)
	except ValueError as e:  # signature verification failure
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
