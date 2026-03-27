import os
from collections.abc import AsyncGenerator
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.gateways import IArxivSourceFetcher, ILatexCompiler, ILatexTranslator
from domain.repositories import IFileStorageRepository, ITranslatedArxivRepository
from infrastructure.arxiv_api import ArxivSourceFetcher
from infrastructure.latex_subprocess import LatexCompiler
from infrastructure.mistral import MistralLatexTranslator
from infrastructure.postgres import (
    PostgresTranslatedArxivRepository,
    create_async_session_factory,
    get_async_session,
)
from infrastructure.supabase import SupabaseStorageRepository
from usecase import (
    ArxivRedirecter,
    SaveTranslatedArxivUsecase,
    TranslateArxivPaper,
)

load_dotenv()

# --------------------------------------
# Environment variables
# --------------------------------------
_postgres_url = os.getenv('POSTGRES_URL', '')
_supabase_url = os.getenv('SUPABASE_URL', '')
_supabase_key = os.getenv('SUPABASE_KEY', '')
_bucket_name = os.getenv('BUCKET_NAME', '')
_mistral_api_key = os.getenv('MISTRAL_API_KEY', '')

if not all([_postgres_url, _supabase_url, _supabase_key, _bucket_name, _mistral_api_key]):
    raise ValueError('One or more required environment variables are not set')

# --------------------------------------
# Async session factory (singleton)
# --------------------------------------
_async_session_factory = create_async_session_factory(_postgres_url)


# --------------------------------------
# DB Session (request-scoped)
# --------------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Yield a request-scoped AsyncSession."""
    async for session in get_async_session(_async_session_factory):
        yield session


# --------------------------------------
# Repository providers
# --------------------------------------
async def get_translated_arxiv_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ITranslatedArxivRepository:
    return PostgresTranslatedArxivRepository(session=session)


def get_file_storage_repository() -> IFileStorageRepository:
    return SupabaseStorageRepository(
        supabase_url=_supabase_url, supabase_key=_supabase_key, bucket_name=_bucket_name
    )


# --------------------------------------
# Gateway providers
# --------------------------------------
def get_arxiv_source_fetcher() -> IArxivSourceFetcher:
    return ArxivSourceFetcher()


def get_latex_compiler() -> ILatexCompiler:
    return LatexCompiler()


def get_latex_translator() -> ILatexTranslator:
    return MistralLatexTranslator(api_key=_mistral_api_key)


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
