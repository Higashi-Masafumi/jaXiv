from domain.entities.auth_user import AuthUser
from domain.repositories.i_usage_repository import IUsageRepository
from domain.value_objects.usage_limit import UsageLimit
from domain.value_objects.user_role import UserRole

# Anonymous chat is gated at the controller layer (login required); the value
# is kept here for completeness but never reached at runtime.
_BLOG_MONTHLY_LIMIT_BY_ROLE: dict[UserRole, UsageLimit] = {
	UserRole.ANONYMOUS: UsageLimit.of(3),
	UserRole.FREE: UsageLimit.of(10),
	UserRole.PAID: UsageLimit.of(100),
}

_CHAT_DAILY_LIMIT_BY_ROLE: dict[UserRole, UsageLimit] = {
	UserRole.ANONYMOUS: UsageLimit.of(0),
	UserRole.FREE: UsageLimit.of(30),
	UserRole.PAID: UsageLimit.unlimited(),
}


class RoleBasedUsageRepository(IUsageRepository):
	"""Usage limit repository with hardcoded per-role limits per feature."""

	async def get_blog_monthly_limit(self, auth_user: AuthUser) -> UsageLimit:
		return _BLOG_MONTHLY_LIMIT_BY_ROLE.get(auth_user.role, UsageLimit.of(0))

	async def get_chat_daily_limit(self, auth_user: AuthUser) -> UsageLimit:
		return _CHAT_DAILY_LIMIT_BY_ROLE.get(auth_user.role, UsageLimit.of(0))
