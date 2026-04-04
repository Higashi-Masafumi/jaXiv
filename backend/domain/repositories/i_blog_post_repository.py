from abc import ABC, abstractmethod

from domain.entities.blog import BlogPost


class IBlogPostRepository(ABC):
	"""Repository for persisting and retrieving blog posts."""

	@abstractmethod
	async def find_by_paper_id(self, paper_id: str) -> BlogPost | None:
		"""
		Find a blog post by paper ID.

		Args:
		    paper_id: The arXiv paper ID.

		Returns:
		    The blog post, or None if not found.
		"""
		...

	@abstractmethod
	async def find_all(self, page: int, page_size: int) -> list[BlogPost]:
		"""Find blog posts ordered by created_at descending with pagination."""
		...

	@abstractmethod
	async def count_all(self) -> int:
		"""Return the total number of blog posts."""
		...

	@abstractmethod
	async def save(self, blog_post: BlogPost) -> BlogPost:
		"""
		Save a blog post.

		Args:
		    blog_post: The blog post to save.

		Returns:
		    The saved blog post.
		"""
		...
