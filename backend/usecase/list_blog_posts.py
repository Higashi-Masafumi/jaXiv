from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository


class ListBlogPostsUseCase:
	"""Use case for retrieving all blog posts."""

	def __init__(self, blog_post_repository: IBlogPostRepository):
		self._blog_post_repository = blog_post_repository

	async def execute(self) -> list[BlogPost]:
		return await self._blog_post_repository.find_all()
