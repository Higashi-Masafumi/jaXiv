from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict


class BillingAccountRef(BaseModel):
	"""Reference to an external billing-provider account (Stripe).

	Domain code only knows that there is *some* external billing account
	identified by an opaque ``customer_id`` (and optionally an active
	subscription). Provider-specific naming (``stripe_*``) lives in the
	infrastructure layer.
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
