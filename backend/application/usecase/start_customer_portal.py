from pydantic import HttpUrl

from domain.entities.auth_user import AuthUser
from domain.errors._base import DomainNotFoundError
from domain.gateways.i_billing_gateway import IBillingGateway, PortalSession
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.user_id import UserId


class NoBillingAccountError(DomainNotFoundError):
	"""Raised when a user has no billing-provider customer record yet."""

	def __init__(self, user_id: UserId) -> None:
		super().__init__(f'No billing account for user {user_id.root}')
		self.user_id = user_id


class StartCustomerPortalUseCase:
	"""Issue a Customer Portal URL for the current user.

	The return URL is derived from the request's frontend origin, so the
	backend doesn't need a frontend-base-URL setting.
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
	) -> PortalSession:
		sub = await self._repo.find_by_user_id(auth_user.user_id)
		if sub is None or sub.billing is None:
			raise NoBillingAccountError(auth_user.user_id)
		base = str(frontend_origin).rstrip('/')
		return await self._billing.create_portal_session(
			stripe_customer_id=sub.billing.customer_id,
			return_url=HttpUrl(f'{base}/pricing'),
		)
