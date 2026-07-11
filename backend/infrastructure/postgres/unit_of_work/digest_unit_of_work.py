from application.unit_of_works import DigestUnitOfWork
from domain.repositories import (
	IAuthUserRepository,
	IBlogPostRepository,
	IDigestDeliveryRepository,
)
from infrastructure.postgres.repositories import (
	PostgresAuthUserRepository,
	PostgresBlogPostRepository,
	PostgresDigestDeliveryRepository,
)

from ._base import SqlAlchemyUnitOfWorkBase


class PostgresDigestUnitOfWork(SqlAlchemyUnitOfWorkBase, DigestUnitOfWork):
	@property
	def auth_users(self) -> IAuthUserRepository:
		return PostgresAuthUserRepository(session=self._session)

	@property
	def digest_deliveries(self) -> IDigestDeliveryRepository:
		return PostgresDigestDeliveryRepository(session=self._session)

	@property
	def blog_posts(self) -> IBlogPostRepository:
		return PostgresBlogPostRepository(session=self._session)
