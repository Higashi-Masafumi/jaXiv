from abc import ABC, abstractmethod

from domain.entities.blog import BlogPost
from domain.value_objects.user_id import UserId


class IBlogPostRepository(ABC):
	"""Repository for persisting and retrieving blog posts."""

	@abstractmethod
	async def find_by_paper_id(self, paper_id: str) -> BlogPost | None:
		"""Find a blog post by paper ID."""
		...

	@abstractmethod
	async def find_all(self, page: int, page_size: int) -> list[BlogPost]:
		"""Find arXiv blog posts ordered by created_at descending with pagination."""
		...

	@abstractmethod
	async def count_all(self) -> int:
		"""Return the total number of arXiv blog posts."""
		...

	@abstractmethod
	async def find_all_by_user(self, user_id: UserId, page: int, page_size: int) -> list[BlogPost]:
		"""Find a user's PDF blog posts ordered by created_at descending with pagination."""
		...

	@abstractmethod
	async def count_all_by_user(self, user_id: UserId) -> int:
		"""Return the total number of PDF blog posts for a given user."""
		...

	@abstractmethod
	async def save(self, blog_post: BlogPost) -> BlogPost:
		"""Save a blog post and return the persisted entity."""
		...
