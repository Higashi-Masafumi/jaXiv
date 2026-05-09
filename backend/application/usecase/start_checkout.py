from pydantic import HttpUrl

from domain.entities.auth_user import AuthUser
from domain.gateways.i_billing_gateway import CheckoutSession, IBillingGateway
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)


class StartCheckoutUseCase:
	"""Issue a billing-provider Checkout session URL for the current user."""

	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
		success_url: HttpUrl,
		cancel_url: HttpUrl,
	) -> None:
		self._billing = billing
		self._repo = repo
		self._success_url = success_url
		self._cancel_url = cancel_url

	async def execute(self, *, auth_user: AuthUser) -> CheckoutSession:
		existing = await self._repo.find_by_user_id(auth_user.user_id)
		customer_id = existing.billing.customer_id if existing and existing.billing else None
		return await self._billing.create_checkout_session(
			user_id=auth_user.user_id,
			stripe_customer_id=customer_id,
			success_url=self._success_url,
			cancel_url=self._cancel_url,
		)
