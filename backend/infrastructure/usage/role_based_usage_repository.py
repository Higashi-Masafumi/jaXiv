from domain.entities.auth_user import AuthUser
from domain.repositories.i_usage_repository import IUsageRepository
from domain.value_objects.usage_limit import UsageLimit
from domain.value_objects.user_role import UserRole


class RoleBasedUsageRepository(IUsageRepository):
	"""Usage limit repository with hardcoded per-role limits per feature."""

	async def get_blog_monthly_limit(self, auth_user: AuthUser) -> UsageLimit:
		if auth_user.role == UserRole.PAID:
			return UsageLimit.of(100)
		if auth_user.role == UserRole.FREE:
			return UsageLimit.of(10)
		return UsageLimit.of(3)

	async def get_chat_daily_limit(self, auth_user: AuthUser) -> UsageLimit:
		if auth_user.role == UserRole.PAID:
			return UsageLimit.unlimited()
		if auth_user.role == UserRole.FREE:
			return UsageLimit.of(30)
		return UsageLimit.of(0)
