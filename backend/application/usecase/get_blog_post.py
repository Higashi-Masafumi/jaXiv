from logging import getLogger

from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository


class GetBlogPostUseCase:
	"""Use case for retrieving a blog post by its paper ID."""

	def __init__(self, blog_post_repository: IBlogPostRepository):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository

	async def execute(self, paper_id: str) -> BlogPost | None:
		return await self._blog_post_repository.find_by_paper_id(paper_id)
