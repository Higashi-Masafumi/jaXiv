import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from domain.entities.blog import BlogPost
from domain.entities.blog_stream import (
	CompleteBlogChunk,
	ErrorBlogChunk,
	IntermediateBlogChunk,
	TypedBlogChunk,
)
from domain.gateways import IArxivSourceFetcher, IBlogPostGenerator
from domain.repositories import IBlogPostRepository, IFigureStorageRepository
from domain.value_objects import ArxivPaperId


class GenerateBlogPostUseCase:
	"""Use case for generating and persisting a blog post from an arXiv paper."""

	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		blog_post_generator: IBlogPostGenerator,
		arxiv_source_fetcher: IArxivSourceFetcher,
		figure_storage_repository: IFigureStorageRepository,
	):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository
		self._blog_post_generator = blog_post_generator
		self._arxiv_source_fetcher = arxiv_source_fetcher
		self._figure_storage_repository = figure_storage_repository

	async def execute(
		self, arxiv_paper_id: ArxivPaperId, output_dir: str
	) -> AsyncIterator[TypedBlogChunk]:
		"""
		Generate (or return cached) a blog post for the given arXiv paper.

		Yields progress chunks and finishes with either CompleteBlogChunk or ErrorBlogChunk.
		"""
		try:
			# 1. Return cached blog post if available
			existing = await self._blog_post_repository.find_by_paper_id(arxiv_paper_id.root)
			if existing is not None:
				self._logger.info('Returning cached blog post for %s', arxiv_paper_id.root)
				yield CompleteBlogChunk(
					message='キャッシュ済みのブログを返します。',
					paper_id=existing.paper_id,
				)
				return

			# 2. Fetch paper metadata
			yield IntermediateBlogChunk(message='メタデータを取得しています...')
			paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
				paper_id=arxiv_paper_id
			)

			# 3. Download LaTeX source
			yield IntermediateBlogChunk(message='LaTeXソースを取得しています...')
			source_dir = Path(os.path.join(output_dir, arxiv_paper_id.root))
			self._arxiv_source_fetcher.fetch_tex_source(
				paper_id=arxiv_paper_id, output_dir=output_dir
			)

			# 4. Upload figures to Supabase Storage
			yield IntermediateBlogChunk(message='レイアウト分析中...')
			figure_urls = await self._figure_storage_repository.upload_figures(
				paper_id=arxiv_paper_id.root,
				source_dir=source_dir,
			)

			# 5. Generate Markdown blog post via Gemini
			yield IntermediateBlogChunk(message='ブログを生成しています...')
			markdown_content = await self._blog_post_generator.generate(
				paper_metadata=paper_metadata,
				latex_source_dir=source_dir,
				figure_urls=figure_urls,
			)

			# 6. Persist and return the blog post
			yield IntermediateBlogChunk(message='保存しています...')
			now = datetime.now(UTC)
			blog_post = BlogPost(
				paper_id=arxiv_paper_id.root,
				title=paper_metadata.title,
				summary=paper_metadata.summary,
				authors=[a.name for a in paper_metadata.authors],
				source_url=str(paper_metadata.source_url),
				content=markdown_content,
				created_at=now,
				updated_at=now,
			)
			saved = await self._blog_post_repository.save(blog_post)
			yield CompleteBlogChunk(
				message='ブログの生成が完了しました。',
				paper_id=saved.paper_id,
			)
		except Exception as e:
			self._logger.exception('Blog generation failed for arXiv %s', arxiv_paper_id.root)
			yield ErrorBlogChunk(
				message='ブログの生成に失敗しました。',
				error_details=str(e),
			)
