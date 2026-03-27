import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.gateways import (
	IArxivSourceFetcher,
	IBlogPostGenerator,
	ILatexCompiler,
	ILatexTranslator,
)
from domain.repositories import (
	IBlogPostRepository,
	IFileStorageRepository,
	ITranslatedArxivRepository,
)
from infrastructure.arxiv_api import ArxivSourceFetcher
from infrastructure.gemini import GeminiBlogPostGenerator
from infrastructure.latex_subprocess import LatexCompiler
from infrastructure.mistral import MistralLatexTranslator
from infrastructure.postgres import (
	PostgresBlogPostRepository,
	PostgresTranslatedArxivRepository,
	get_async_session,
)
from infrastructure.supabase import SupabaseFigureStorageRepository, SupabaseStorageRepository
from usecase import (
	ArxivRedirecter,
	GenerateBlogPostUsecase,
	GetBlogPostUsecase,
	SaveTranslatedArxivUsecase,
	TranslateArxivPaper,
)

load_dotenv()

# --------------------------------------
# Environment variables
# --------------------------------------
_supabase_url = os.getenv('SUPABASE_URL', '')
_supabase_key = os.getenv('SUPABASE_KEY', '')
_bucket_name = os.getenv('BUCKET_NAME', '')
_mistral_api_key = os.getenv('MISTRAL_API_KEY', '')
_gemini_api_key = os.getenv('GEMINI_API_KEY', '')
_blog_figures_bucket_name = os.getenv('BLOG_FIGURES_BUCKET_NAME', '')

if not all([_supabase_url, _supabase_key, _bucket_name, _mistral_api_key, _gemini_api_key]):
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
		supabase_url=_supabase_url, supabase_key=_supabase_key, bucket_name=_bucket_name
	)


async def get_blog_post_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IBlogPostRepository:
	return PostgresBlogPostRepository(session=session)


# --------------------------------------
# Gateway providers
# --------------------------------------
def get_arxiv_source_fetcher() -> IArxivSourceFetcher:
	return ArxivSourceFetcher()


def get_latex_compiler() -> ILatexCompiler:
	return LatexCompiler()


def get_latex_translator() -> ILatexTranslator:
	return MistralLatexTranslator(api_key=_mistral_api_key)


def get_blog_post_generator() -> IBlogPostGenerator:
	return GeminiBlogPostGenerator(api_key=_gemini_api_key)


def get_figure_storage_repository() -> SupabaseFigureStorageRepository:
	return SupabaseFigureStorageRepository(
		supabase_url=_supabase_url,
		supabase_key=_supabase_key,
		bucket_name=_blog_figures_bucket_name,
	)


# --------------------------------------
# Use case providers
# --------------------------------------
async def get_arxiv_redirecter(
	translated_arxiv_repository: Annotated[
		ITranslatedArxivRepository, Depends(get_translated_arxiv_repository)
	],
) -> ArxivRedirecter:
	return ArxivRedirecter(
		translated_arxiv_repository=translated_arxiv_repository,
	)


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
) -> SaveTranslatedArxivUsecase:
	return SaveTranslatedArxivUsecase(
		translated_arxiv_repository=translated_arxiv_repository,
		file_storage_repository=file_storage_repository,
		arxiv_source_fetcher=arxiv_source_fetcher,
	)


async def get_get_blog_post(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
) -> GetBlogPostUsecase:
	return GetBlogPostUsecase(
		blog_post_repository=blog_post_repository,
		arxiv_source_fetcher=arxiv_source_fetcher,
	)


async def get_generate_blog_post(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
	blog_post_generator: Annotated[IBlogPostGenerator, Depends(get_blog_post_generator)],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
	figure_storage_repository: Annotated[
		SupabaseFigureStorageRepository, Depends(get_figure_storage_repository)
	],
) -> GenerateBlogPostUsecase:
	return GenerateBlogPostUsecase(
		blog_post_repository=blog_post_repository,
		blog_post_generator=blog_post_generator,
		arxiv_source_fetcher=arxiv_source_fetcher,
		figure_storage_repository=figure_storage_repository,
	)
