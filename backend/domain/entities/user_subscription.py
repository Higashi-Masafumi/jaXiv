from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from domain.value_objects.billing_account import BillingAccount
from domain.value_objects.user_id import UserId

from domain.value_objects.subscription_plan import SubscriptionPlan


class UserSubscription(BaseModel):
	"""A user's subscription record.

	The optional ``billing`` field references an external billing provider
	when the user has gone through Checkout at least once. Plain free users
	have ``billing=None``.
	"""

	model_config = ConfigDict(frozen=False)

	user_id: UserId
	plan: SubscriptionPlan = SubscriptionPlan.FREE
	billing: BillingAccount | None = None
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

	def is_active_paid(self, *, now: datetime | None = None) -> bool:
		if self.plan != SubscriptionPlan.PAID:
			return False
		if self.billing is None:
			# Plan is paid but no billing reference — treat as active.
			return True
		return self.billing.is_within_period(now=now)
