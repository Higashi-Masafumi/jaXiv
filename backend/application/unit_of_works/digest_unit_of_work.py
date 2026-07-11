from abc import abstractmethod

from domain.repositories import (
	IAuthUserRepository,
	IBlogPostRepository,
	IDigestDeliveryRepository,
	ITopicSubscriptionRepository,
)

from ._base import UnitOfWork


class DigestUnitOfWork(UnitOfWork):
	"""UoW bundling the repositories needed to build and record weekly digests."""

	@property
	@abstractmethod
	def topic_subscriptions(self) -> ITopicSubscriptionRepository:
		raise NotImplementedError

	@property
	@abstractmethod
	def digest_deliveries(self) -> IDigestDeliveryRepository:
		raise NotImplementedError

	@property
	@abstractmethod
	def blog_posts(self) -> IBlogPostRepository:
		raise NotImplementedError

	@property
	@abstractmethod
	def auth_users(self) -> IAuthUserRepository:
		raise NotImplementedError
