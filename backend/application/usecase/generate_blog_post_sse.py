import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from application.unit_of_works import BlogPostUnitOfWork
from domain.entities.blog import BlogPost
from domain.entities.blog_stream import (
	CompleteBlogChunk,
	ErrorBlogChunk,
	IntermediateBlogChunk,
	TypedBlogChunk,
)
from domain.gateways import IArxivSourceFetcher, IBlogPostGenerator
from domain.repositories import IFigureStorageRepository
from domain.value_objects import ArxivPaperId


class GenerateBlogPostSSEUseCase:
	"""Use case for generating and persisting a blog post with an SSE-safe UoW."""

	def __init__(
		self,
		blog_post_unit_of_work: BlogPostUnitOfWork,
		blog_post_generator: IBlogPostGenerator,
		arxiv_source_fetcher: IArxivSourceFetcher,
		figure_storage_repository: IFigureStorageRepository,
	):
		self._logger = getLogger(__name__)
		self._uow = blog_post_unit_of_work
		self._blog_post_generator = blog_post_generator
		self._arxiv_source_fetcher = arxiv_source_fetcher
		self._figure_storage_repository = figure_storage_repository

	async def execute(
		self, arxiv_paper_id: ArxivPaperId, output_dir: str
	) -> AsyncIterator[TypedBlogChunk]:
		try:
			async with self._uow as uow:
				existing = await uow.blog_posts_repository.find_by_paper_id(arxiv_paper_id.root)
			if existing is not None:
				self._logger.info('Returning cached blog post for %s', arxiv_paper_id.root)
				yield CompleteBlogChunk(
					message='キャッシュ済みのブログを返します。',
					paper_id=existing.paper_id,
				)
				return

			yield IntermediateBlogChunk(message='メタデータを取得しています...')
			paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
				paper_id=arxiv_paper_id
			)

			yield IntermediateBlogChunk(message='LaTeXソースを取得しています...')
			source_dir = Path(os.path.join(output_dir, arxiv_paper_id.root))
			self._arxiv_source_fetcher.fetch_tex_source(
				paper_id=arxiv_paper_id, output_dir=output_dir
			)

			yield IntermediateBlogChunk(message='レイアウト分析中...')
			figure_urls = await self._figure_storage_repository.upload_figures(
				paper_id=arxiv_paper_id.root,
				source_dir=source_dir,
			)

			yield IntermediateBlogChunk(message='ブログを生成しています...')
			markdown_content = await self._blog_post_generator.generate(
				paper_metadata=paper_metadata,
				latex_source_dir=source_dir,
				figure_urls=figure_urls,
			)

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
			async with self._uow as uow:
				saved = await uow.blog_posts_repository.save(blog_post)
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
