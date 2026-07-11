from abc import abstractmethod

from domain.repositories import (
	IAuthUserRepository,
	IBlogPostRepository,
	IDigestDeliveryRepository,
)

from ._base import UnitOfWork


class DigestUnitOfWork(UnitOfWork):
	"""UoW for the per-subscriber delivery step: read matches then record in one transaction."""

	@property
	@abstractmethod
	def auth_users(self) -> IAuthUserRepository:
		raise NotImplementedError

	@property
	@abstractmethod
	def digest_deliveries(self) -> IDigestDeliveryRepository:
		raise NotImplementedError

	@property
	@abstractmethod
	def blog_posts(self) -> IBlogPostRepository:
		raise NotImplementedError
