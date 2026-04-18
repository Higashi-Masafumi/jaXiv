import asyncio
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from domain.entities.blog import BlogPost
from domain.errors.domain_error import GenerationLimitExceededError
from domain.value_objects.blog_source_type import BlogSourceType
from domain.value_objects.user_id import UserId
from domain.entities.document_chunk import DocumentFigureChunk, DocumentTextChunk
from domain.entities.figure import UploadedFigure
from domain.gateways import IPdfBlogPostGenerator, IPdfChunkAnalyzer, IPdfFigureAnalyzer
from domain.repositories import (
	IBlogPostRepository,
	IFigureChunkRepository,
	IFigureStorageRepository,
	ITextChunkRepository,
)
from domain.value_objects import PdfPaperId
from domain.value_objects.image_url import ImageUrl

_FREE_MONTHLY_LIMIT = 10


class GenerateBlogPostFromPdfUseCase:
	"""Use case for generating and persisting a blog post from an uploaded PDF.

	Gemini extracts the paper metadata (title, authors, summary) **and**
	generates the blog post in a single structured-output API call.
	A UUID7-based paper_id is generated upfront so that figure uploads
	can use the final storage prefix immediately.

	Figure analysis and text chunking are run in parallel via asyncio.gather.
	"""

	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		blog_post_generator: IPdfBlogPostGenerator,
		figure_analyzer: IPdfFigureAnalyzer,
		figure_storage_repository: IFigureStorageRepository,
		chunk_analyzer: IPdfChunkAnalyzer,
		text_chunk_repository: ITextChunkRepository,
		figure_chunk_repository: IFigureChunkRepository,
	):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository
		self._blog_post_generator = blog_post_generator
		self._figure_analyzer = figure_analyzer
		self._figure_storage_repository = figure_storage_repository
		self._chunk_analyzer = chunk_analyzer
		self._text_chunk_repository = text_chunk_repository
		self._figure_chunk_repository = figure_chunk_repository

	async def execute(self, pdf_path: Path, user_id: UserId | None = None) -> BlogPost:
		paper_id = PdfPaperId.generate()
		try:
			if user_id is not None:
				month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
				count = await self._blog_post_repository.count_generated_by_user(user_id, since=month_start)
				if count >= _FREE_MONTHLY_LIMIT:
					raise GenerationLimitExceededError(monthly_count=count, limit=_FREE_MONTHLY_LIMIT)
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

			figures_with_embedding, text_chunks = await asyncio.gather(
				self._figure_analyzer.analyze_figures(pdf_path),
				self._chunk_analyzer.analyze_chunks(pdf_path),
			)

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

			self._logger.info(
				'Indexed %d text chunks and %d figure chunks for paper %s',
				len(text_chunks),
				len(uploaded_figures),
				paper_id.root,
			)

			metadata, markdown_content = await self._blog_post_generator.generate_from_pdf(
				pdf_path=pdf_path,
				figures=uploaded_figures,
			)

			now = datetime.now(UTC)
			blog_post = BlogPost(
				paper_id=paper_id.root,
				title=metadata.title,
				summary=metadata.summary,
				authors=metadata.authors,
				source_url=source_url,
				content=markdown_content,
				source_type=BlogSourceType('pdf'),
				user_id=user_id,
				created_at=now,
				updated_at=now,
			)
			return await self._blog_post_repository.save(blog_post)
		except Exception:
			self._logger.exception('Blog generation from PDF failed')
			raise
