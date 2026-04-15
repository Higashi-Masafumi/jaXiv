import uuid

from application.usecase.list_blog_posts import PaginatedBlogPosts
from domain.repositories import IBlogPostRepository


class ListMyBlogPostsUseCase:
	"""Use case for retrieving a user's own PDF blog posts (paginated)."""

	def __init__(self, blog_post_repository: IBlogPostRepository):
		self._blog_post_repository = blog_post_repository

	async def execute(
		self, user_id: uuid.UUID, page: int, page_size: int
	) -> PaginatedBlogPosts:
		items = await self._blog_post_repository.find_all_by_user(
			user_id=user_id, page=page, page_size=page_size
		)
		total = await self._blog_post_repository.count_all_by_user(user_id=user_id)
		total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
		return PaginatedBlogPosts(
			items=items,
			total=total,
			page=page,
			page_size=page_size,
			total_pages=total_pages,
		)
