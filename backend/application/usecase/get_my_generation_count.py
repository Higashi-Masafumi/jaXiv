import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from domain.repositories import IBlogPostRepository
from domain.value_objects.user_id import UserId

_FREE_MONTHLY_LIMIT = 10


@dataclass(frozen=True)
class GenerationCount:
	monthly: int
	total: int
	limit: int


class GetMyGenerationCountUseCase:
	def __init__(self, blog_post_repository: IBlogPostRepository):
		self._repo = blog_post_repository

	async def execute(self, user_id: UserId) -> GenerationCount:
		month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		monthly, total = await asyncio.gather(
			self._repo.count_generated_by_user(user_id, since=month_start),
			self._repo.count_generated_by_user(user_id),
		)
		return GenerationCount(monthly=monthly, total=total, limit=_FREE_MONTHLY_LIMIT)
