from abc import ABC, abstractmethod

from domain.entities.auth_user import AuthUser


class IUsageRepository(ABC):
	"""Repository for querying per-role generation limits."""

	@abstractmethod
	async def get_max_usage_count(self, auth_user: AuthUser) -> int:
		"""Return the monthly generation limit for the given user's role."""
		...
