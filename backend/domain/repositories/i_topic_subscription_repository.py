from abc import ABC, abstractmethod

from domain.entities.topic_subscription import TopicSubscription
from domain.value_objects.user_id import UserId


class ITopicSubscriptionRepository(ABC):
	"""Repository for users' weekly-digest topic subscriptions."""

	@abstractmethod
	async def find_by_user_id(self, user_id: UserId) -> TopicSubscription | None:
		"""Find a user's topic subscription by their user ID."""
		raise NotImplementedError

	@abstractmethod
	async def upsert(self, subscription: TopicSubscription) -> TopicSubscription:
		"""Create or update a user's topic subscription and return the persisted entity."""
		raise NotImplementedError
