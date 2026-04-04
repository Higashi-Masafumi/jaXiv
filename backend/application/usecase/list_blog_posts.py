from pydantic import BaseModel

from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository


class PaginatedBlogPosts(BaseModel):
	items: list[BlogPost]
	total: int
	page: int
	page_size: int
	total_pages: int


class ListBlogPostsUseCase:
	"""Use case for retrieving paginated blog posts."""

	def __init__(self, blog_post_repository: IBlogPostRepository):
		self._blog_post_repository = blog_post_repository

	async def execute(self, page: int, page_size: int) -> PaginatedBlogPosts:
		items = await self._blog_post_repository.find_all(page=page, page_size=page_size)
		total = await self._blog_post_repository.count_all()
		total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
		return PaginatedBlogPosts(
			items=items,
			total=total,
			page=page,
			page_size=page_size,
			total_pages=total_pages,
		)
