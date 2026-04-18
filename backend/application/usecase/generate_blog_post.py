import asyncio
import base64
import os
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from domain.entities.blog import BlogPost
from domain.errors.domain_error import GenerationLimitExceededError
from domain.value_objects.blog_source_type import BlogSourceType
from domain.value_objects.user_id import UserId
from domain.entities.document_chunk import DocumentFigureChunk, DocumentTextChunk
from domain.gateways import (
	IArxivSourceFetcher,
	IBlogPostGenerator,
	IImageEmbedder,
	IPdfChunkAnalyzer,
	ImageEmbedItem,
)
from domain.repositories import (
	IBlogPostRepository,
	IFigureChunkRepository,
	IFigureStorageRepository,
	ITextChunkRepository,
)
from domain.value_objects import ArxivPaperId
from domain.value_objects.image_url import ImageUrl

_EMBED_EXTENSIONS: frozenset[str] = frozenset({'.png', '.jpg', '.jpeg', '.gif', '.webp'})
_ANONYMOUS_MONTHLY_LIMIT = 3
_FREE_MONTHLY_LIMIT = 10


class GenerateBlogPostUseCase:
	"""Use case for generating and persisting a blog post from an arXiv paper."""

	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		blog_post_generator: IBlogPostGenerator,
		arxiv_source_fetcher: IArxivSourceFetcher,
		figure_storage_repository: IFigureStorageRepository,
		chunk_analyzer: IPdfChunkAnalyzer,
		image_embedder: IImageEmbedder,
		text_chunk_repository: ITextChunkRepository,
		figure_chunk_repository: IFigureChunkRepository,
	):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository
		self._blog_post_generator = blog_post_generator
		self._arxiv_source_fetcher = arxiv_source_fetcher
		self._figure_storage_repository = figure_storage_repository
		self._chunk_analyzer = chunk_analyzer
		self._image_embedder = image_embedder
		self._text_chunk_repository = text_chunk_repository
		self._figure_chunk_repository = figure_chunk_repository

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
		output_dir: str,
		user_id: UserId | None = None,
		is_anonymous: bool = True,
	) -> BlogPost:
		"""Generate (or return cached) a blog post for the given arXiv paper."""
		try:
			existing = await self._blog_post_repository.find_by_paper_id(arxiv_paper_id.root)
			if existing is not None:
				self._logger.info('Returning cached blog post for %s', arxiv_paper_id.root)
				return existing

			if user_id is not None:
				limit = _ANONYMOUS_MONTHLY_LIMIT if is_anonymous else _FREE_MONTHLY_LIMIT
				month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
				count = await self._blog_post_repository.count_generated_by_user(user_id, since=month_start)
				if count >= limit:
					raise GenerationLimitExceededError(monthly_count=count, limit=limit)

			paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
				paper_id=arxiv_paper_id
			)
			pdf_url = str(paper_metadata.source_url)

			source_dir = Path(os.path.join(output_dir, arxiv_paper_id.root))
			self._arxiv_source_fetcher.fetch_tex_source(
				paper_id=arxiv_paper_id, output_dir=output_dir
			)

			image_files = sorted(
				f for f in source_dir.rglob('*') if f.suffix.lower() in _EMBED_EXTENSIONS
			)
			image_items = [
				ImageEmbedItem(
					image_base64=base64.b64encode(f.read_bytes()).decode(),
					caption=None,
				)
				for f in image_files
			]

			figure_urls, text_chunks, image_embeddings = await asyncio.gather(
				self._figure_storage_repository.upload_figures(
					paper_id=arxiv_paper_id.root,
					source_dir=source_dir,
				),
				self._chunk_analyzer.analyze_chunks_from_url(pdf_url),
				self._image_embedder.embed_images(image_items),
			)

			for chunk in text_chunks:
				await self._text_chunk_repository.save(
					DocumentTextChunk(
						chunk_type='text',
						paper_id=arxiv_paper_id,
						text=chunk.text,
						page_number=chunk.page_number,
						embeddings=chunk.embeddings,
					)
				)

			for img_file, embedding in zip(image_files, image_embeddings, strict=False):
				url = figure_urls.get(img_file.name)
				if url is None:
					continue
				await self._figure_chunk_repository.save(
					DocumentFigureChunk(
						chunk_type='figure',
						paper_id=arxiv_paper_id,
						image_url=ImageUrl(url),
						caption=None,
						page_number=0,
						image_embeddings=embedding.image_embeddings,
						caption_embeddings=embedding.caption_embeddings,
					)
				)

			self._logger.info(
				'Indexed %d text chunks and %d figures for arXiv %s',
				len(text_chunks),
				len(image_files),
				arxiv_paper_id.root,
			)

			markdown_content = await self._blog_post_generator.generate(
				paper_metadata=paper_metadata,
				latex_source_dir=source_dir,
				figure_urls=figure_urls,
			)

			now = datetime.now(UTC)
			blog_post = BlogPost(
				paper_id=arxiv_paper_id.root,
				title=paper_metadata.title,
				summary=paper_metadata.summary,
				authors=[a.name for a in paper_metadata.authors],
				source_url=str(paper_metadata.source_url),
				content=markdown_content,
				source_type=BlogSourceType('arxiv'),
				user_id=user_id,
				created_at=now,
				updated_at=now,
			)
			return await self._blog_post_repository.save(blog_post)
		except Exception:
			self._logger.exception('Blog generation failed for arXiv %s', arxiv_paper_id.root)
			raise
