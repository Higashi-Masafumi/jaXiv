import os
from functools import lru_cache
from typing import Annotated

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from application.usecase import (
	ArxivRedirector,
	ArxivRedirectorSSEUseCase,
	GenerateBlogPostFromPdfUseCase,
	GenerateBlogPostFromPdfSSEUseCase,
	GenerateBlogPostUseCase,
	GenerateBlogPostSSEUseCase,
	GetBlogPostUseCase,
	ListBlogPostsUseCase,
	SaveTranslatedArxivUseCase,
	SaveTranslatedArxivSSEUseCase,
	TranslateArxivPaper,
)
from application.unit_of_works import BlogPostUnitOfWork, TranslatedArxivUnitOfWork

from domain.gateways import (
	IArxivSourceFetcher,
	IBlogPostGenerator,
	IImageEmbedder,
	ILatexCompiler,
	ILatexTranslator,
	IPdfBlogPostGenerator,
	IPdfChunkAnalyzer,
	IPdfFigureAnalyzer,
	IPdfFigureExtractor,
)
from domain.repositories import (
	IBlogPostRepository,
	IFigureChunkRepository,
	IFigureStorageRepository,
	IFileStorageRepository,
	ITextChunkRepository,
	ITranslatedArxivRepository,
)
from infrastructure.arxiv_api import ArxivSourceFetcher
from infrastructure.gemini import GeminiBlogPostGenerator
from infrastructure.latex_subprocess import LatexCompiler
from infrastructure.mistral import MistralLatexTranslator
from infrastructure.pdf import (
	HttpImageEmbedder,
	HttpPdfChunkAnalyzer,
	HttpPdfFigureAnalyzer,
	HttpPdfFigureExtractor,
)
from infrastructure.postgres import (
	PostgresBlogPostUnitOfWork,
	PostgresTranslatedArxivUnitOfWork,
	create_async_session_factory,
	get_async_session,
)
from infrastructure.postgres.repositories import (
	PostgresBlogPostRepository,
	PostgresTranslatedArxivRepository,
)
from infrastructure.qdrant import QdrantFigureChunkRepository, QdrantTextChunkRepository
from infrastructure.supabase import SupabaseFigureStorageRepository, SupabaseStorageRepository

load_dotenv()

# --------------------------------------
# Environment variables
# --------------------------------------
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
BUCKET_NAME = os.getenv('BUCKET_NAME', '')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
BLOG_FIGURES_BUCKET_NAME = os.getenv('BLOG_FIGURES_BUCKET_NAME', '')
LAYOUT_ANALYSIS_URL = os.getenv('LAYOUT_ANALYSIS_URL', 'http://localhost:8001')
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')

if not all([SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME, MISTRAL_API_KEY, GEMINI_API_KEY]):
	raise ValueError('One or more required environment variables are not set')


# --------------------------------------
# Repository providers
# --------------------------------------
async def get_translated_arxiv_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ITranslatedArxivRepository:
	return PostgresTranslatedArxivRepository(session=session)


def get_file_storage_repository() -> IFileStorageRepository:
	return SupabaseStorageRepository(
		supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY, bucket_name=BUCKET_NAME
	)


async def get_blog_post_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IBlogPostRepository:
	return PostgresBlogPostRepository(session=session)


def get_sse_blog_post_unit_of_work() -> BlogPostUnitOfWork:
	return PostgresBlogPostUnitOfWork(session_factory=create_async_session_factory())


def get_sse_translated_arxiv_unit_of_work() -> TranslatedArxivUnitOfWork:
	return PostgresTranslatedArxivUnitOfWork(session_factory=create_async_session_factory())


def get_figure_storage_repository() -> IFigureStorageRepository:
	return SupabaseFigureStorageRepository(
		supabase_url=SUPABASE_URL,
		supabase_key=SUPABASE_KEY,
		bucket_name=BLOG_FIGURES_BUCKET_NAME,
	)


@lru_cache
def get_qdrant_client() -> QdrantClient:
	return QdrantClient(url=QDRANT_URL)


def get_figure_chunk_repository(
	client: Annotated[QdrantClient, Depends(get_qdrant_client)],
) -> IFigureChunkRepository:
	return QdrantFigureChunkRepository(client=client)


def get_text_chunk_repository(
	client: Annotated[QdrantClient, Depends(get_qdrant_client)],
) -> ITextChunkRepository:
	return QdrantTextChunkRepository(client=client)


# --------------------------------------
# Gateway providers
# --------------------------------------
def get_arxiv_source_fetcher() -> IArxivSourceFetcher:
	return ArxivSourceFetcher()


def get_latex_compiler() -> ILatexCompiler:
	return LatexCompiler()


def get_latex_translator() -> ILatexTranslator:
	return MistralLatexTranslator(api_key=MISTRAL_API_KEY)


def get_blog_post_generator() -> IBlogPostGenerator:
	return GeminiBlogPostGenerator(api_key=GEMINI_API_KEY)


def get_pdf_blog_post_generator() -> IPdfBlogPostGenerator:
	return GeminiBlogPostGenerator(api_key=GEMINI_API_KEY)


def get_pdf_figure_extractor() -> IPdfFigureExtractor:
	return HttpPdfFigureExtractor(service_url=LAYOUT_ANALYSIS_URL)


def get_pdf_chunk_analyzer() -> IPdfChunkAnalyzer:
	return HttpPdfChunkAnalyzer(service_url=LAYOUT_ANALYSIS_URL)


def get_pdf_figure_analyzer() -> IPdfFigureAnalyzer:
	return HttpPdfFigureAnalyzer(service_url=LAYOUT_ANALYSIS_URL)


def get_image_embedder() -> IImageEmbedder:
	return HttpImageEmbedder(service_url=LAYOUT_ANALYSIS_URL)


# --------------------------------------
# Use case providers
# --------------------------------------
async def get_arxiv_redirector(
	translated_arxiv_repository: Annotated[
		ITranslatedArxivRepository, Depends(get_translated_arxiv_repository)
	],
) -> ArxivRedirector:
	return ArxivRedirector(
		translated_arxiv_repository=translated_arxiv_repository,
	)


def get_sse_arxiv_redirector(
	translated_arxiv_unit_of_work: Annotated[
		TranslatedArxivUnitOfWork, Depends(get_sse_translated_arxiv_unit_of_work)
	],
) -> ArxivRedirectorSSEUseCase:
	return ArxivRedirectorSSEUseCase(translated_arxiv_unit_of_work=translated_arxiv_unit_of_work)


def get_translate_arxiv_paper(
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
	latex_compiler: Annotated[ILatexCompiler, Depends(get_latex_compiler)],
	latex_translator: Annotated[ILatexTranslator, Depends(get_latex_translator)],
) -> TranslateArxivPaper:
	return TranslateArxivPaper(
		arxiv_source_fetcher=arxiv_source_fetcher,
		latex_compiler=latex_compiler,
		latex_translator=latex_translator,
	)


async def get_save_translated_arxiv(
	translated_arxiv_repository: Annotated[
		ITranslatedArxivRepository, Depends(get_translated_arxiv_repository)
	],
	file_storage_repository: Annotated[
		IFileStorageRepository, Depends(get_file_storage_repository)
	],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
) -> SaveTranslatedArxivUseCase:
	return SaveTranslatedArxivUseCase(
		translated_arxiv_repository=translated_arxiv_repository,
		file_storage_repository=file_storage_repository,
		arxiv_source_fetcher=arxiv_source_fetcher,
	)


def get_sse_save_translated_arxiv(
	translated_arxiv_unit_of_work: Annotated[
		TranslatedArxivUnitOfWork, Depends(get_sse_translated_arxiv_unit_of_work)
	],
	file_storage_repository: Annotated[
		IFileStorageRepository, Depends(get_file_storage_repository)
	],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
) -> SaveTranslatedArxivSSEUseCase:
	return SaveTranslatedArxivSSEUseCase(
		translated_arxiv_unit_of_work=translated_arxiv_unit_of_work,
		file_storage_repository=file_storage_repository,
		arxiv_source_fetcher=arxiv_source_fetcher,
	)


async def get_get_blog_post(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
) -> GetBlogPostUseCase:
	return GetBlogPostUseCase(blog_post_repository=blog_post_repository)


async def get_list_blog_posts(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
) -> ListBlogPostsUseCase:
	return ListBlogPostsUseCase(blog_post_repository=blog_post_repository)


async def get_generate_blog_post(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
	blog_post_generator: Annotated[IBlogPostGenerator, Depends(get_blog_post_generator)],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
	figure_storage_repository: Annotated[
		IFigureStorageRepository, Depends(get_figure_storage_repository)
	],
	chunk_analyzer: Annotated[IPdfChunkAnalyzer, Depends(get_pdf_chunk_analyzer)],
	image_embedder: Annotated[IImageEmbedder, Depends(get_image_embedder)],
	text_chunk_repository: Annotated[ITextChunkRepository, Depends(get_text_chunk_repository)],
	figure_chunk_repository: Annotated[
		IFigureChunkRepository, Depends(get_figure_chunk_repository)
	],
) -> GenerateBlogPostUseCase:
	return GenerateBlogPostUseCase(
		blog_post_repository=blog_post_repository,
		blog_post_generator=blog_post_generator,
		arxiv_source_fetcher=arxiv_source_fetcher,
		figure_storage_repository=figure_storage_repository,
		chunk_analyzer=chunk_analyzer,
		image_embedder=image_embedder,
		text_chunk_repository=text_chunk_repository,
		figure_chunk_repository=figure_chunk_repository,
	)


def get_sse_generate_blog_post(
	blog_post_unit_of_work: Annotated[BlogPostUnitOfWork, Depends(get_sse_blog_post_unit_of_work)],
	blog_post_generator: Annotated[IBlogPostGenerator, Depends(get_blog_post_generator)],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
	figure_storage_repository: Annotated[
		IFigureStorageRepository, Depends(get_figure_storage_repository)
	],
	chunk_analyzer: Annotated[IPdfChunkAnalyzer, Depends(get_pdf_chunk_analyzer)],
	image_embedder: Annotated[IImageEmbedder, Depends(get_image_embedder)],
	text_chunk_repository: Annotated[ITextChunkRepository, Depends(get_text_chunk_repository)],
	figure_chunk_repository: Annotated[
		IFigureChunkRepository, Depends(get_figure_chunk_repository)
	],
) -> GenerateBlogPostSSEUseCase:
	return GenerateBlogPostSSEUseCase(
		blog_post_unit_of_work=blog_post_unit_of_work,
		blog_post_generator=blog_post_generator,
		arxiv_source_fetcher=arxiv_source_fetcher,
		figure_storage_repository=figure_storage_repository,
		chunk_analyzer=chunk_analyzer,
		image_embedder=image_embedder,
		text_chunk_repository=text_chunk_repository,
		figure_chunk_repository=figure_chunk_repository,
	)


async def get_generate_blog_post_from_pdf(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
	blog_post_generator: Annotated[IPdfBlogPostGenerator, Depends(get_pdf_blog_post_generator)],
	figure_analyzer: Annotated[IPdfFigureAnalyzer, Depends(get_pdf_figure_analyzer)],
	figure_storage_repository: Annotated[
		IFigureStorageRepository, Depends(get_figure_storage_repository)
	],
	chunk_analyzer: Annotated[IPdfChunkAnalyzer, Depends(get_pdf_chunk_analyzer)],
	text_chunk_repository: Annotated[ITextChunkRepository, Depends(get_text_chunk_repository)],
	figure_chunk_repository: Annotated[
		IFigureChunkRepository, Depends(get_figure_chunk_repository)
	],
) -> GenerateBlogPostFromPdfUseCase:
	return GenerateBlogPostFromPdfUseCase(
		blog_post_repository=blog_post_repository,
		blog_post_generator=blog_post_generator,
		figure_analyzer=figure_analyzer,
		figure_storage_repository=figure_storage_repository,
		chunk_analyzer=chunk_analyzer,
		text_chunk_repository=text_chunk_repository,
		figure_chunk_repository=figure_chunk_repository,
	)


def get_sse_generate_blog_post_from_pdf(
	blog_post_unit_of_work: Annotated[BlogPostUnitOfWork, Depends(get_sse_blog_post_unit_of_work)],
	blog_post_generator: Annotated[IPdfBlogPostGenerator, Depends(get_pdf_blog_post_generator)],
	figure_analyzer: Annotated[IPdfFigureAnalyzer, Depends(get_pdf_figure_analyzer)],
	figure_storage_repository: Annotated[
		IFigureStorageRepository, Depends(get_figure_storage_repository)
	],
	chunk_analyzer: Annotated[IPdfChunkAnalyzer, Depends(get_pdf_chunk_analyzer)],
	text_chunk_repository: Annotated[ITextChunkRepository, Depends(get_text_chunk_repository)],
	figure_chunk_repository: Annotated[
		IFigureChunkRepository, Depends(get_figure_chunk_repository)
	],
) -> GenerateBlogPostFromPdfSSEUseCase:
	return GenerateBlogPostFromPdfSSEUseCase(
		blog_post_unit_of_work=blog_post_unit_of_work,
		blog_post_generator=blog_post_generator,
		figure_analyzer=figure_analyzer,
		figure_storage_repository=figure_storage_repository,
		chunk_analyzer=chunk_analyzer,
		text_chunk_repository=text_chunk_repository,
		figure_chunk_repository=figure_chunk_repository,
	)
