from application.unit_of_works import BlogPostUnitOfWork
from domain.repositories import IBlogPostRepository
from infrastructure.postgres.repositories import PostgresBlogPostRepository

from ._base import SqlAlchemyUnitOfWorkBase


class PostgresBlogPostUnitOfWork(SqlAlchemyUnitOfWorkBase, BlogPostUnitOfWork):
	@property
	def blog_posts_repository(self) -> IBlogPostRepository:
		return PostgresBlogPostRepository(session=self._session)
