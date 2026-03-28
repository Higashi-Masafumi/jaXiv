import os
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from domain.entities.blog import BlogPost
from domain.gateways import IArxivSourceFetcher, IBlogPostGenerator
from domain.repositories import IBlogPostRepository
from domain.value_objects import ArxivPaperId
from infrastructure.supabase import SupabaseFigureStorageRepository


class GenerateBlogPostUseCase:
	"""Use case for generating and persisting a blog post from an arXiv paper."""

	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		blog_post_generator: IBlogPostGenerator,
		arxiv_source_fetcher: IArxivSourceFetcher,
		figure_storage_repository: SupabaseFigureStorageRepository,
	):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository
		self._blog_post_generator = blog_post_generator
		self._arxiv_source_fetcher = arxiv_source_fetcher
		self._figure_storage_repository = figure_storage_repository

	async def execute(self, arxiv_paper_id: ArxivPaperId, output_dir: str) -> BlogPost:
		"""
		Generate (or return cached) a blog post for the given arXiv paper.

		Args:
		    arxiv_paper_id: The arXiv paper ID.
		    output_dir: Local directory to extract LaTeX source into.

		Returns:
		    The generated (or cached) BlogPost.
		"""
		# 1. Return cached blog post if available
		existing = await self._blog_post_repository.find_by_paper_id(arxiv_paper_id.value)
		if existing is not None:
			self._logger.info('Returning cached blog post for %s', arxiv_paper_id.value)
			return existing

		# 2. Fetch paper metadata
		paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(paper_id=arxiv_paper_id)

		# 3. Download LaTeX source
		source_dir = Path(os.path.join(output_dir, arxiv_paper_id.value))
		self._arxiv_source_fetcher.fetch_tex_source(paper_id=arxiv_paper_id, output_dir=output_dir)

		# 4. Upload figures to Supabase Storage
		figure_urls = await self._figure_storage_repository.upload_figures(
			paper_id=arxiv_paper_id.value,
			source_dir=source_dir,
		)

		# 5. Generate Markdown blog post via Gemini
		markdown_content = await self._blog_post_generator.generate(
			paper_metadata=paper_metadata,
			latex_source_dir=source_dir,
			figure_urls=figure_urls,
		)

		# 6. Persist and return the blog post
		now = datetime.now(UTC)
		blog_post = BlogPost(
			paper_id=arxiv_paper_id.value,
			content=markdown_content,
			created_at=now,
			updated_at=now,
		)
		return await self._blog_post_repository.save(blog_post)
