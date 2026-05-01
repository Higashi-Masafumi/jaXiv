from __future__ import annotations

from pydantic import BaseModel, ConfigDict, HttpUrl


class FrontendUrls(BaseModel):
	"""Resolved frontend URLs the application redirects users to.

	Construction lives in the infrastructure layer; domain/application code
	receives this value object and never builds URLs itself.
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
