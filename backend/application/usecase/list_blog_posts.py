import asyncio

from pydantic import BaseModel, computed_field

from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository


class PaginatedBlogPosts(BaseModel):
	items: list[BlogPost]
	total: int
	page: int
	page_size: int

	@computed_field
	@property
	def total_pages(self) -> int:
		if self.page_size == 0:
			return 0
		return (self.total + self.page_size - 1) // self.page_size


class ListBlogPostsUseCase:
	"""Use case for retrieving paginated blog posts."""

	def __init__(self, blog_post_repository: IBlogPostRepository):
		self._blog_post_repository = blog_post_repository

	async def execute(self, page: int, page_size: int) -> PaginatedBlogPosts:
		items, total = await asyncio.gather(
			self._blog_post_repository.find_all(page=page, page_size=page_size),
			self._blog_post_repository.count_all(),
		)
		return PaginatedBlogPosts(items=items, total=total, page=page, page_size=page_size)
