from domain.entities.auth_user import AuthUser
from domain.gateways.i_billing_gateway import CheckoutSession, IBillingGateway
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.frontend_urls import FrontendUrls


class StartCheckoutUseCase:
	"""Issue a billing-provider Checkout session URL for the current user."""

	def __init__(
		self,
		billing: IBillingGateway,
		repo: IUserSubscriptionRepository,
		urls: FrontendUrls,
	) -> None:
		self._billing = billing
		self._repo = repo
		self._urls = urls

	async def execute(self, *, auth_user: AuthUser) -> CheckoutSession:
		existing = await self._repo.find_by_user_id(auth_user.user_id)
		customer_id = existing.billing.customer_id if existing and existing.billing else None
		return await self._billing.create_checkout_session(
			user_id=auth_user.user_id,
			stripe_customer_id=customer_id,
			success_url=self._urls.billing_success,
			cancel_url=self._urls.billing_cancel,
		)
