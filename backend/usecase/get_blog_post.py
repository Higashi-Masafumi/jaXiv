from dataclasses import dataclass
from logging import getLogger

from domain.entities.arxiv import ArxivPaperMetadata
from domain.entities.blog import BlogPost
from domain.errors import ArxivPaperNotFoundError
from domain.gateways import IArxivSourceFetcher
from domain.repositories import IBlogPostRepository
from domain.value_objects import ArxivPaperId


@dataclass
class BlogPostWithMetadata:
	blog_post: BlogPost
	paper_metadata: ArxivPaperMetadata


class GetBlogPostUseCase:
	"""Use case for retrieving a blog post along with its paper metadata."""

	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		arxiv_source_fetcher: IArxivSourceFetcher,
	):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository
		self._arxiv_source_fetcher = arxiv_source_fetcher

	async def execute(self, arxiv_paper_id: ArxivPaperId) -> BlogPostWithMetadata | None:
		"""
		Return the blog post and its paper metadata.

		Returns None if the blog post does not exist yet.
		Metadata is always sourced from the arXiv API.
		"""
		blog_post = await self._blog_post_repository.find_by_paper_id(arxiv_paper_id.value)
		if blog_post is None:
			return None

		self._logger.info('Fetching metadata from arXiv API: %s', arxiv_paper_id.value)
		try:
			paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
				paper_id=arxiv_paper_id
			)
		except ArxivPaperNotFoundError:
			self._logger.warning('Paper %s not found on arXiv', arxiv_paper_id.value)
			paper_metadata = None

		if paper_metadata is None:
			# Return blog post with empty metadata placeholders
			from pydantic import HttpUrl

			paper_metadata = ArxivPaperMetadata(
				paper_id=arxiv_paper_id,
				title=arxiv_paper_id.value,
				summary='',
				published_date=blog_post.created_at,
				authors=[],
				source_url=HttpUrl(f'https://arxiv.org/abs/{arxiv_paper_id.value}'),
			)

		return BlogPostWithMetadata(blog_post=blog_post, paper_metadata=paper_metadata)
