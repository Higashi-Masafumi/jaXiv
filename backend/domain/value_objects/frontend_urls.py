from __future__ import annotations

from pydantic import BaseModel, ConfigDict, HttpUrl


class FrontendUrls(BaseModel):
	"""Resolved URLs of frontend pages the backend redirects users to.

	Used by the billing flow:

	- ``billing_success`` / ``billing_cancel``: pages Stripe Checkout
	  redirects to after the user completes / cancels the payment flow.
	- ``pricing``: page Stripe Customer Portal returns to.

	Construction (from ``FRONTEND_BASE_URL``) lives in the infrastructure
	layer's DI provider; domain/application code receives this value
	object so URL strings never have to be assembled in use cases or
	controllers.
	"""

	model_config = ConfigDict(frozen=True)

	pricing: HttpUrl
	billing_success: HttpUrl
	billing_cancel: HttpUrl

	@classmethod
	def from_base(cls, base_url: str) -> 'FrontendUrls':
		base = base_url.rstrip('/')
		return cls(
			pricing=HttpUrl(f'{base}/pricing'),
			billing_success=HttpUrl(f'{base}/billing/success'),
			billing_cancel=HttpUrl(f'{base}/billing/cancel'),
		)
