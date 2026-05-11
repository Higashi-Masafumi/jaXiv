from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from application.usecase import (
	GetMySubscriptionUseCase,
	HandleStripeWebhookUseCase,
	MySubscriptionView,
	StartCheckoutUseCase,
	StartCustomerPortalUseCase,
)
from application.usecase.start_customer_portal import NoBillingAccountError
from domain.entities.auth_user import AuthUser
from infrastructure.dependencies import (
	get_get_my_subscription_use_case,
	get_handle_stripe_webhook_use_case,
	get_required_auth_user,
	get_start_checkout_use_case,
	get_start_customer_portal_use_case,
)

router = APIRouter(prefix='/api/v1/billing')


class MySubscriptionResponse(BaseModel):
	plan: Literal['free', 'paid']
	current_period_end: str | None
	cancel_at_period_end: bool
	has_billing_account: bool

	@classmethod
	def from_view(cls, view: MySubscriptionView) -> 'MySubscriptionResponse':
		return cls(
			plan=view.plan,
			current_period_end=view.current_period_end.isoformat()
			if view.current_period_end
			else None,
			cancel_at_period_end=view.cancel_at_period_end,
			has_billing_account=view.has_billing_account,
		)


class RedirectUrlResponse(BaseModel):
	url: HttpUrl


@router.get('/me', response_model=MySubscriptionResponse)
async def get_my_subscription(
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[GetMySubscriptionUseCase, Depends(get_get_my_subscription_use_case)],
) -> MySubscriptionResponse:
	view = await use_case.execute(auth_user=auth_user)
	return MySubscriptionResponse.from_view(view)


@router.post('/checkout-session', response_model=RedirectUrlResponse)
async def create_checkout_session(
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[StartCheckoutUseCase, Depends(get_start_checkout_use_case)],
) -> RedirectUrlResponse:
	session = await use_case.execute(auth_user=auth_user)
	return RedirectUrlResponse(url=session.url)


@router.post('/portal-session', response_model=RedirectUrlResponse)
async def create_portal_session(
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[StartCustomerPortalUseCase, Depends(get_start_customer_portal_use_case)],
) -> RedirectUrlResponse:
	try:
		session = await use_case.execute(auth_user=auth_user)
	except NoBillingAccountError as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
	return RedirectUrlResponse(url=session.url)


@router.post('/webhook', status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
	request: Request,
	use_case: Annotated[HandleStripeWebhookUseCase, Depends(get_handle_stripe_webhook_use_case)],
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
