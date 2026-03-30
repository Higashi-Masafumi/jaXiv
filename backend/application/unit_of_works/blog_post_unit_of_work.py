from abc import abstractmethod

from domain.repositories import IBlogPostRepository

from ._base import UnitOfWork


class BlogPostUnitOfWork(UnitOfWork):
	"""ブログ投稿の永続化用 UoW。"""

	@property
	@abstractmethod
	def blog_posts_repository(self) -> IBlogPostRepository:
		raise NotImplementedError
