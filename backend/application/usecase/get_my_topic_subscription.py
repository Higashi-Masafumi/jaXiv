from domain.entities.topic_subscription import TopicSubscription
from domain.repositories import ITopicSubscriptionRepository
from domain.value_objects.user_id import UserId


class GetMyTopicSubscriptionUseCase:
	"""Return the caller's topic subscription, or ``None`` if not subscribed yet."""

	def __init__(self, repo: ITopicSubscriptionRepository) -> None:
		self._repo = repo

	async def execute(self, user_id: UserId) -> TopicSubscription | None:
		return await self._repo.find_by_user_id(user_id)
