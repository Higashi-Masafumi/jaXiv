from datetime import UTC, datetime

from pydantic import BaseModel

from domain.entities.auth_user import AuthUser
from domain.repositories import IChatThreadRepository, IUsageRepository


class ChatDailyCount(BaseModel):
	daily: int
	limit: int | None  # None means unlimited


class GetMyChatDailyCountUseCase:
	def __init__(
		self,
		chat_thread_repository: IChatThreadRepository,
		usage_repository: IUsageRepository,
	):
		self._repo = chat_thread_repository
		self._usage_repo = usage_repository

	async def execute(self, auth_user: AuthUser) -> ChatDailyCount:
		today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
		limit = await self._usage_repo.get_chat_daily_limit(auth_user)
		daily = await self._repo.count_user_messages(auth_user.user_id, since=today_start)
		return ChatDailyCount(daily=daily, limit=limit.value)
