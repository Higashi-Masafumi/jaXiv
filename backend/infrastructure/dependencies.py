import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from application.usecase import (
	ArxivRedirector,
	ArxivRedirectorSSEUseCase,
	GenerateBlogPostFromPdfUseCase,
	GenerateBlogPostFromPdfSSEUseCase,
	GenerateBlogPostUseCase,
	GenerateBlogPostSSEUseCase,
	GetBlogPostUseCase,
	GetMyGenerationCountUseCase,
	ListBlogPostsUseCase,
	ListMyBlogPostsUseCase,
	RagSearchImageUseCase,
	RagSearchTextUseCase,
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
	IQueryEmbeddingGateway,
)
from domain.entities.auth_user import AuthUser
from domain.repositories import (
	IBlogPostRepository,
	IFigureChunkRepository,
	IFigureStorageRepository,
	IFileStorageRepository,
	ITextChunkRepository,
	ITranslatedArxivRepository,
	IUsageRepository,
)
from domain.value_objects.user_id import UserId
from domain.value_objects.user_role import UserRole
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
from infrastructure.auth import (
	get_user_id_from_payload,
	verify_supabase_jwt,
)
from infrastructure.layout_analysis import HttpQueryEmbeddingGateway
from infrastructure.qdrant import QdrantFigureChunkRepository, QdrantTextChunkRepository
from infrastructure.supabase import SupabaseFigureStorageRepository, SupabaseStorageRepository
from infrastructure.usage.hardcoded_usage_repository import HardcodedUsageRepository


# --------------------------------------
# Auth dependencies
# --------------------------------------
async def get_optional_user_id(
	credentials: Annotated[
		HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))
	],
) -> uuid.UUID | None:
	"""Extract user_id from Bearer JWT if present; return None if missing."""
	if credentials is None:
		return None
	payload = verify_supabase_jwt(credentials.credentials)
	return get_user_id_from_payload(payload)


async def get_auth_user(
	credentials: Annotated[
		HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))
	],
) -> AuthUser | None:
	"""Build AuthUser from Bearer JWT; return None if no token provided."""
	if credentials is None:
		return None
	payload = verify_supabase_jwt(credentials.credentials)
	user_id = get_user_id_from_payload(payload)
	role = UserRole.ANONYMOUS if payload.get('is_anonymous', False) else UserRole.FREE
	return AuthUser(user_id=UserId(user_id), role=role)


async def get_required_auth_user(
	credentials: Annotated[
		HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))
	],
) -> AuthUser:
	"""Build AuthUser from Bearer JWT; raise 401 if missing, 403 if anonymous."""
	if credentials is None:
		raise HTTPException(status_code=401, detail='Authentication required.')
	payload = verify_supabase_jwt(credentials.credentials)
	if payload.get('is_anonymous', False):
		raise HTTPException(
			status_code=403,
			detail='Full authentication is required. Please sign in with Google.',
		)
	user_id = get_user_id_from_payload(payload)
	return AuthUser(user_id=UserId(user_id), role=UserRole.FREE)


async def get_required_user_id(
	credentials: Annotated[
		HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))
	],
) -> uuid.UUID:
	"""Extract user_id from Bearer JWT; raise 401 if missing, 403 if anonymous."""
	if credentials is None:
		raise HTTPException(status_code=401, detail='Authentication required.')
	payload = verify_supabase_jwt(credentials.credentials)
	if payload.get('is_anonymous', False):
		raise HTTPException(
			status_code=403,
			detail='Full authentication is required. Please sign in with Google.',
		)
	return get_user_id_from_payload(payload)


# --------------------------------------
# Repository providers
# --------------------------------------
async def get_translated_arxiv_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ITranslatedArxivRepository:
	return PostgresTranslatedArxivRepository(session=session)


def get_file_storage_repository() -> IFileStorageRepository:
	return SupabaseStorageRepository()


async def get_blog_post_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IBlogPostRepository:
	return PostgresBlogPostRepository(session=session)


def get_sse_blog_post_unit_of_work() -> BlogPostUnitOfWork:
	return PostgresBlogPostUnitOfWork(session_factory=create_async_session_factory())


def get_sse_translated_arxiv_unit_of_work() -> TranslatedArxivUnitOfWork:
	return PostgresTranslatedArxivUnitOfWork(session_factory=create_async_session_factory())


def get_figure_storage_repository() -> IFigureStorageRepository:
	return SupabaseFigureStorageRepository()


def get_figure_chunk_repository() -> IFigureChunkRepository:
	return QdrantFigureChunkRepository()


def get_text_chunk_repository() -> ITextChunkRepository:
	return QdrantTextChunkRepository()


def get_usage_repository() -> IUsageRepository:
	return HardcodedUsageRepository()


def get_query_embedding_gateway() -> IQueryEmbeddingGateway:
	return HttpQueryEmbeddingGateway()


def get_rag_search_text_use_case(
	query_embedding: Annotated[IQueryEmbeddingGateway, Depends(get_query_embedding_gateway)],
	text_chunk_repository: Annotated[ITextChunkRepository, Depends(get_text_chunk_repository)],
) -> RagSearchTextUseCase:
	return RagSearchTextUseCase(
		query_embedding=query_embedding,
		text_chunk_repository=text_chunk_repository,
	)


def get_rag_search_image_use_case(
	query_embedding: Annotated[IQueryEmbeddingGateway, Depends(get_query_embedding_gateway)],
	figure_chunk_repository: Annotated[
		IFigureChunkRepository, Depends(get_figure_chunk_repository)
	],
) -> RagSearchImageUseCase:
	return RagSearchImageUseCase(
		query_embedding=query_embedding,
		figure_chunk_repository=figure_chunk_repository,
	)


# --------------------------------------
# Gateway providers
# --------------------------------------
def get_arxiv_source_fetcher() -> IArxivSourceFetcher:
	return ArxivSourceFetcher()


def get_latex_compiler() -> ILatexCompiler:
	return LatexCompiler()


def get_latex_translator() -> ILatexTranslator:
	return MistralLatexTranslator()


def get_blog_post_generator() -> IBlogPostGenerator:
	return GeminiBlogPostGenerator()


def get_pdf_blog_post_generator() -> IPdfBlogPostGenerator:
	return GeminiBlogPostGenerator()


def get_pdf_figure_extractor() -> IPdfFigureExtractor:
	return HttpPdfFigureExtractor()


def get_pdf_chunk_analyzer() -> IPdfChunkAnalyzer:
	return HttpPdfChunkAnalyzer()


def get_pdf_figure_analyzer() -> IPdfFigureAnalyzer:
	return HttpPdfFigureAnalyzer()


def get_image_embedder() -> IImageEmbedder:
	return HttpImageEmbedder()


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


async def get_list_my_blog_posts(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
) -> ListMyBlogPostsUseCase:
	return ListMyBlogPostsUseCase(blog_post_repository=blog_post_repository)


async def get_get_my_generation_count(
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
) -> GetMyGenerationCountUseCase:
	return GetMyGenerationCountUseCase(
		blog_post_repository=blog_post_repository,
		usage_repository=usage_repository,
	)


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
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
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
		usage_repository=usage_repository,
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
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
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
		usage_repository=usage_repository,
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
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
) -> GenerateBlogPostFromPdfUseCase:
	return GenerateBlogPostFromPdfUseCase(
		blog_post_repository=blog_post_repository,
		blog_post_generator=blog_post_generator,
		figure_analyzer=figure_analyzer,
		figure_storage_repository=figure_storage_repository,
		chunk_analyzer=chunk_analyzer,
		text_chunk_repository=text_chunk_repository,
		figure_chunk_repository=figure_chunk_repository,
		usage_repository=usage_repository,
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
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
) -> GenerateBlogPostFromPdfSSEUseCase:
	return GenerateBlogPostFromPdfSSEUseCase(
		blog_post_unit_of_work=blog_post_unit_of_work,
		blog_post_generator=blog_post_generator,
		figure_analyzer=figure_analyzer,
		figure_storage_repository=figure_storage_repository,
		chunk_analyzer=chunk_analyzer,
		text_chunk_repository=text_chunk_repository,
		figure_chunk_repository=figure_chunk_repository,
		usage_repository=usage_repository,
	)
