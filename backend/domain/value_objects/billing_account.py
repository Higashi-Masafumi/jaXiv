from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict


class BillingAccount(BaseModel):
	"""A user's account at the external billing provider (Stripe).

	``customer_id`` and ``subscription_id`` are opaque identifiers issued by
	the provider; the period fields capture when the current paid period
	expires and whether the user has already requested cancellation.
	"""

	model_config = ConfigDict(frozen=True)

	customer_id: str
	subscription_id: str | None = None
	current_period_end: datetime | None = None
	cancel_at_period_end: bool = False

	def is_within_period(self, *, now: datetime | None = None) -> bool:
		"""True if the current billing period has not ended yet."""
		if self.current_period_end is None:
			return True
		return (now or datetime.now(UTC)) < self.current_period_end
