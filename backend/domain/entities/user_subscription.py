from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.value_objects.user_id import UserId

SubscriptionPlan = Literal['free', 'paid']


class UserSubscription(BaseModel):
	model_config = ConfigDict(frozen=False)

	user_id: UserId
	plan: SubscriptionPlan = 'free'
	stripe_customer_id: str | None = None
	stripe_subscription_id: str | None = None
	current_period_end: datetime | None = None
	cancel_at_period_end: bool = False
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

	def is_active_paid(self, *, now: datetime | None = None) -> bool:
		if self.plan != 'paid':
			return False
		if self.current_period_end is None:
			return True
		return (now or datetime.now(UTC)) < self.current_period_end
