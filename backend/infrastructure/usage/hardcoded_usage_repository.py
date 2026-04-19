from domain.entities.auth_user import AuthUser
from domain.repositories.i_usage_repository import IUsageRepository
from domain.value_objects.user_role import UserRole


class HardcodedUsageRepository(IUsageRepository):
	"""Usage limit repository with hardcoded per-role limits."""

	async def get_max_usage_count(self, auth_user: AuthUser) -> int:
		if auth_user.role == UserRole.ANONYMOUS:
			return 3
		return 10  # UserRole.FREE
