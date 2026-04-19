import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from application.unit_of_works import BlogPostUnitOfWork
from domain.entities.auth_user import AuthUser
from domain.entities.blog import BlogPost
from domain.value_objects.blog_source_type import BlogSourceType
from domain.entities.blog_stream import (
	CompleteBlogChunk,
	ErrorBlogChunk,
	IntermediateBlogChunk,
	TypedBlogChunk,
)
from domain.entities.document_chunk import DocumentFigureChunk, DocumentTextChunk
from domain.entities.figure import UploadedFigure
from domain.gateways import IPdfBlogPostGenerator, IPdfChunkAnalyzer, IPdfFigureAnalyzer
from domain.repositories import (
	IFigureChunkRepository,
	IFigureStorageRepository,
	ITextChunkRepository,
	IUsageRepository,
)
from domain.value_objects import PdfPaperId
from domain.value_objects.image_url import ImageUrl


class GenerateBlogPostFromPdfSSEUseCase:
	"""Use case for generating and persisting a PDF blog post with an SSE-safe UoW."""

	def __init__(
		self,
		blog_post_unit_of_work: BlogPostUnitOfWork,
		blog_post_generator: IPdfBlogPostGenerator,
		figure_analyzer: IPdfFigureAnalyzer,
		figure_storage_repository: IFigureStorageRepository,
		chunk_analyzer: IPdfChunkAnalyzer,
		text_chunk_repository: ITextChunkRepository,
		figure_chunk_repository: IFigureChunkRepository,
		usage_repository: IUsageRepository,
	):
		self._logger = getLogger(__name__)
		self._uow = blog_post_unit_of_work
		self._blog_post_generator = blog_post_generator
		self._figure_analyzer = figure_analyzer
		self._figure_storage_repository = figure_storage_repository
		self._chunk_analyzer = chunk_analyzer
		self._text_chunk_repository = text_chunk_repository
		self._figure_chunk_repository = figure_chunk_repository
		self._usage_repository = usage_repository

	async def execute(
		self, pdf_path: Path, auth_user: AuthUser
	) -> AsyncIterator[TypedBlogChunk]:
		paper_id = PdfPaperId.generate()
		try:
			max_count = await self._usage_repository.get_max_usage_count(auth_user)
			month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
			async with self._uow as uow:
				count = await uow.blog_posts_repository.count_generated_by_user(auth_user.user_id, since=month_start)
			if count >= max_count:
				yield ErrorBlogChunk(message='limit_exceeded', error_details='limit_exceeded')
				return

			yield IntermediateBlogChunk(message='PDFをアップロードしています...')
			source_url: str | None
			try:
				source_url = await self._figure_storage_repository.upload_pdf(
					paper_id=paper_id.root,
					pdf_path=pdf_path,
				)
			except Exception:
				self._logger.warning(
					'Failed to upload PDF to storage; source_url will be None', exc_info=True
				)
				source_url = None

			yield IntermediateBlogChunk(message='テキスト・図を並列解析中...')
			figures_with_embedding, text_chunks = await asyncio.gather(
				self._figure_analyzer.analyze_figures(pdf_path),
				self._chunk_analyzer.analyze_chunks(pdf_path),
			)

			yield IntermediateBlogChunk(message='図をアップロードしています...')
			uploaded_figures: list[UploadedFigure] = []
			for idx, fig in enumerate(figures_with_embedding):
				fig_label = fig.figure_number if fig.figure_number is not None else idx
				filename = f'fig_p{fig.page_number}_{fig_label}.png'
				try:
					url = await self._figure_storage_repository.upload_figure_bytes(
						paper_id=paper_id.root,
						filename=filename,
						data=fig.image_bytes,
					)
					uploaded_figures.append(
						UploadedFigure(
							url=url,
							caption=fig.caption,
							figure_number=fig.figure_number,
							page_number=fig.page_number,
						)
					)
				except Exception:
					self._logger.warning(
						'Failed to upload figure %s; skipping', filename, exc_info=True
					)

			self._logger.info(
				'Uploaded %d/%d figures for paper %s',
				len(uploaded_figures),
				len(figures_with_embedding),
				paper_id.root,
			)

			yield IntermediateBlogChunk(message='インデックスを登録しています...')
			for chunk in text_chunks:
				await self._text_chunk_repository.save(
					DocumentTextChunk(
						chunk_type='text',
						paper_id=paper_id,
						text=chunk.text,
						page_number=chunk.page_number,
						embeddings=chunk.embeddings,
					)
				)

			for fig, uploaded in zip(figures_with_embedding, uploaded_figures, strict=False):
				await self._figure_chunk_repository.save(
					DocumentFigureChunk(
						chunk_type='figure',
						paper_id=paper_id,
						image_url=ImageUrl(uploaded.url),
						caption=fig.caption,
						page_number=fig.page_number,
						image_embeddings=fig.image_embeddings,
						caption_embeddings=fig.caption_embeddings,
					)
				)

			yield IntermediateBlogChunk(message='ブログを生成しています...')
			metadata, markdown_content = await self._blog_post_generator.generate_from_pdf(
				pdf_path=pdf_path,
				figures=uploaded_figures,
			)

			yield IntermediateBlogChunk(message='保存しています...')
			now = datetime.now(UTC)
			blog_post = BlogPost(
				paper_id=paper_id.root,
				title=metadata.title,
				summary=metadata.summary,
				authors=metadata.authors,
				source_url=source_url,
				content=markdown_content,
				source_type=BlogSourceType('pdf'),
				user_id=auth_user.user_id,
				created_at=now,
				updated_at=now,
			)
			async with self._uow as uow:
				saved = await uow.blog_posts_repository.save(blog_post)
			yield CompleteBlogChunk(message='ブログの生成が完了しました。', paper_id=saved.paper_id)
		except Exception as e:
			self._logger.exception('Blog generation from PDF failed')
			yield ErrorBlogChunk(
				message='ブログの生成に失敗しました。',
				error_details=str(e),
			)
