from domain.entities.topic_subscription import TopicSubscription
from domain.repositories import ITopicSubscriptionRepository
from domain.value_objects.user_id import UserId


class UpsertTopicSubscriptionUseCase:
	"""Create or update the caller's topic subscription.

	Saving keywords implies opting into the digest, so the subscription is
	(re)activated. The repository upsert preserves the existing id/created_at.
	"""

	def __init__(self, repo: ITopicSubscriptionRepository) -> None:
		self._repo = repo

	async def execute(self, user_id: UserId, email: str, keywords: list[str]) -> TopicSubscription:
		subscription = TopicSubscription(user_id=user_id, email=email, keywords=keywords)
		return await self._repo.upsert(subscription)
