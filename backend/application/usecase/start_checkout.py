from pydantic import HttpUrl

from domain.entities.auth_user import AuthUser
from domain.gateways.i_billing_gateway import CheckoutSession, IBillingGateway
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)


class StartCheckoutUseCase:
	"""Issue a billing-provider Checkout session URL for the current user.

	The frontend's origin (where Stripe redirects back after Checkout) is
	taken from the request, not from a backend-side env var. The use case
	owns the route paths users should land on.
	"""

	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
	) -> None:
		self._billing = billing
		self._repo = repo

	async def execute(
		self,
		*,
		auth_user: AuthUser,
		frontend_origin: HttpUrl,
	) -> CheckoutSession:
		base = str(frontend_origin).rstrip('/')
		existing = await self._repo.find_by_user_id(auth_user.user_id)
		customer_id = existing.billing.customer_id if existing and existing.billing else None
		return await self._billing.create_checkout_session(
			user_id=auth_user.user_id,
			stripe_customer_id=customer_id,
			success_url=HttpUrl(f'{base}/billing/success'),
			cancel_url=HttpUrl(f'{base}/billing/cancel'),
		)
