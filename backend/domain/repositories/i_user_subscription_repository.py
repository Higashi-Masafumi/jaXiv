from abc import ABC, abstractmethod

from domain.entities.user_subscription import UserSubscription
from domain.value_objects.user_id import UserId


class IUserSubscriptionRepository(ABC):
	@abstractmethod
	async def find_by_user_id(self, user_id: UserId) -> UserSubscription | None:
		"""Find a user's subscription by their user ID."""
		raise NotImplementedError

	@abstractmethod
	async def upsert(self, subscription: UserSubscription) -> UserSubscription:
		"""Upsert a user's subscription."""
		raise NotImplementedError
