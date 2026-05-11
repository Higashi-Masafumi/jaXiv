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
	) -> None:
		self._billing_gateway = billing
		self._user_subscription_repository = repo

	async def execute(
		self,
		auth_user: AuthUser,
	) -> CheckoutSession:
		existing = await self._user_subscription_repository.find_by_user_id(auth_user.user_id)
		customer_id = existing.billing.customer_id if existing and existing.billing else None
		return await self._billing_gateway.create_checkout_session(
			user_id=auth_user.user_id,
			stripe_customer_id=customer_id,
		)
