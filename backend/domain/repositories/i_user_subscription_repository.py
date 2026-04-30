from abc import ABC, abstractmethod

from domain.entities.user_subscription import UserSubscription
from domain.value_objects.user_id import UserId


class IUserSubscriptionRepository(ABC):
	@abstractmethod
	async def find_by_user_id(self, user_id: UserId) -> UserSubscription | None: ...

	@abstractmethod
	async def find_by_stripe_customer_id(
		self, stripe_customer_id: str
	) -> UserSubscription | None: ...

	@abstractmethod
	async def upsert(self, subscription: UserSubscription) -> UserSubscription: ...
