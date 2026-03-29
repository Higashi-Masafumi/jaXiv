from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path

from domain.entities.blog import BlogPost
from domain.entities.extracted_figure import UploadedFigure
from domain.gateways import IPdfBlogPostGenerator, IPdfFigureExtractor
from domain.repositories import IBlogPostRepository, IFigureStorageRepository
from domain.value_objects import PdfPaperId


class GenerateBlogPostFromPdfUseCase:
	"""Use case for generating and persisting a blog post from an uploaded PDF.

	Gemini extracts the paper metadata (title, authors, summary) **and**
	generates the blog post in a single structured-output API call.
	A UUID7-based paper_id is generated upfront so that figure uploads
	can use the final storage prefix immediately.
	"""

	def __init__(
		self,
		blog_post_repository: IBlogPostRepository,
		blog_post_generator: IPdfBlogPostGenerator,
		figure_extractor: IPdfFigureExtractor,
		figure_storage_repository: IFigureStorageRepository,
	):
		self._logger = getLogger(__name__)
		self._blog_post_repository = blog_post_repository
		self._blog_post_generator = blog_post_generator
		self._figure_extractor = figure_extractor
		self._figure_storage_repository = figure_storage_repository

	async def execute(self, pdf_path: Path) -> BlogPost:
		paper_id = PdfPaperId.generate()

		try:
			source_url: str | None = await self._figure_storage_repository.upload_pdf(
				paper_id=paper_id.root,
				pdf_path=pdf_path,
			)
		except Exception:
			self._logger.warning('Failed to upload PDF to storage; source_url will be None', exc_info=True)
			source_url = None

		extracted_figures = self._figure_extractor.extract_figures(pdf_path)

		uploaded_figures: list[UploadedFigure] = []
		for idx, fig in enumerate(extracted_figures):
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
			len(extracted_figures),
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
			created_at=now,
			updated_at=now,
		)
		return await self._blog_post_repository.save(blog_post)
