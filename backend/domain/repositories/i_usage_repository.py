from abc import ABC, abstractmethod

from domain.entities.auth_user import AuthUser
from domain.value_objects.usage_limit import UsageLimit


class IUsageRepository(ABC):
	"""Repository for resolving per-role usage limits per feature."""

	@abstractmethod
	async def get_blog_monthly_limit(self, auth_user: AuthUser) -> UsageLimit:
		"""Return the monthly blog generation limit for the user's role."""
		...

	@abstractmethod
	async def get_chat_daily_limit(self, auth_user: AuthUser) -> UsageLimit:
		"""Return the daily chat user-message limit for the user's role."""
		...
