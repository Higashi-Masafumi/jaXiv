from datetime import UTC, datetime

from pydantic import BaseModel

from domain.entities.auth_user import AuthUser
from domain.repositories import IBlogPostRepository, IUsageRepository


class GenerationCount(BaseModel):
	monthly: int
	total: int
	limit: int


class GetMyGenerationCountUseCase:
	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		usage_repository: IUsageRepository,
	):
		self._repo = blog_post_repository
		self._usage_repo = usage_repository

	async def execute(self, auth_user: AuthUser) -> GenerationCount:
		month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		limit = await self._usage_repo.get_max_usage_count(auth_user)
		monthly = await self._repo.count_generated_by_user(auth_user.user_id, since=month_start)
		total = await self._repo.count_generated_by_user(auth_user.user_id)
		return GenerationCount(monthly=monthly, total=total, limit=limit)
