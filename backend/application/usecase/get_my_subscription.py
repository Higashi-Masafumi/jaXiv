from datetime import datetime

from pydantic import BaseModel, ConfigDict

from domain.entities.auth_user import AuthUser
from domain.repositories.i_user_subscription_repository import (
	IUserSubscriptionRepository,
)
from domain.value_objects.subscription_plan import SubscriptionPlan


class MySubscriptionView(BaseModel):
	model_config = ConfigDict(frozen=True)

	plan: SubscriptionPlan
	current_period_end: datetime | None
	cancel_at_period_end: bool
	has_billing_account: bool


class GetMySubscriptionUseCase:
	def __init__(self, repo: IUserSubscriptionRepository) -> None:
		self._repo = repo

	async def execute(self, auth_user: AuthUser) -> MySubscriptionView:
		sub = await self._repo.find_by_user_id(auth_user.user_id)
		billing = sub.billing if sub else None
		return MySubscriptionView(
			plan=sub.plan if sub else SubscriptionPlan.FREE,
			current_period_end=billing.current_period_end if billing else None,
			cancel_at_period_end=billing.cancel_at_period_end if billing else False,
			has_billing_account=billing is not None,
		)
