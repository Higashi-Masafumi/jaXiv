import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from application.unit_of_works import (
	BlogPostUnitOfWork,
	ChatThreadUnitOfWork,
)
from application.usecase import (
	ArxivRedirector,
	ChatWithPaperUseCase,
	DeleteChatThreadUseCase,
	GenerateBlogPostFromPdfSSEUseCase,
	GenerateBlogPostFromPdfUseCase,
	GenerateBlogPostSSEUseCase,
	GenerateBlogPostUseCase,
	GetBlogPostUseCase,
	GetChatThreadUseCase,
	GetMyChatDailyCountUseCase,
	GetMyGenerationCountUseCase,
	GetMySubscriptionUseCase,
	HandleStripeWebhookUseCase,
	ListBlogPostsUseCase,
	ListChatThreadsUseCase,
	ListMyBlogPostsUseCase,
	RagSearchImageUseCase,
	RagSearchTextUseCase,
	SaveTranslatedArxivUseCase,
	StartCheckoutUseCase,
	StartCustomerPortalUseCase,
	SuggestFiguresUseCase,
	TranslateArxivPaper,
)
from domain.entities.auth_user import AuthUser
from domain.gateways import (
	IArxivSourceFetcher,
	IBillingGateway,
	IBlogPostGenerator,
	IChatLLMGateway,
	IFigureQueryGenerator,
	IImageEmbedder,
	IPdfBlogPostGenerator,
	IPdfChunkAnalyzer,
	IPdfFigureAnalyzer,
	IPdfFigureExtractor,
	IQueryEmbeddingGateway,
	ITexTranslationGateway,
)
from domain.repositories import (
	IBlogPostRepository,
	IChatThreadRepository,
	IFigureChunkRepository,
	IFigureStorageRepository,
	IFileStorageRepository,
	ITextChunkRepository,
	ITranslatedArxivRepository,
	IUsageRepository,
	IUserSubscriptionRepository,
)
from domain.value_objects.user_id import UserId
from domain.value_objects.user_role import UserRole
from infrastructure.arxiv_api import ArxivSourceFetcher
from infrastructure.auth import (
	get_user_id_from_payload,
	verify_supabase_jwt,
)
from infrastructure.gemini import (
	GeminiBlogPostGenerator,
	GeminiChatLLM,
	GeminiFigureQueryGenerator,
)
from infrastructure.layout_analysis import HttpQueryEmbeddingGateway
from infrastructure.pdf import (
	HttpImageEmbedder,
	HttpPdfChunkAnalyzer,
	HttpPdfFigureAnalyzer,
	HttpPdfFigureExtractor,
)
from infrastructure.postgres import (
	PostgresBlogPostUnitOfWork,
	PostgresChatThreadUnitOfWork,
	create_async_session_factory,
	get_async_session,
)
from infrastructure.postgres.repositories import (
	PostgresBlogPostRepository,
	PostgresChatThreadRepository,
	PostgresTranslatedArxivRepository,
	PostgresUserSubscriptionRepository,
)
from infrastructure.qdrant import QdrantFigureChunkRepository, QdrantTextChunkRepository
from infrastructure.stripe import StripeBillingGateway, StripeConfig, get_stripe_config
from infrastructure.supabase import SupabaseFigureStorageRepository, SupabaseStorageRepository
from infrastructure.tex_translation import HttpTexTranslationGateway
from infrastructure.usage.role_based_usage_repository import RoleBasedUsageRepository


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


async def get_user_subscription_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IUserSubscriptionRepository:
	return PostgresUserSubscriptionRepository(session=session)


async def _resolve_role_from_subscription(
	user_id: uuid.UUID,
	sub_repo: IUserSubscriptionRepository,
) -> UserRole:
	"""Resolve FREE vs PAID by looking up the user's subscription record."""
	subscription = await sub_repo.find_by_user_id(UserId(user_id))
	if subscription is not None and subscription.is_active_paid():
		return UserRole.PAID
	return UserRole.FREE


async def get_auth_user(
	credentials: Annotated[
		HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))
	],
	sub_repo: Annotated[IUserSubscriptionRepository, Depends(get_user_subscription_repository)],
) -> AuthUser:
	"""Build AuthUser from Bearer JWT; raise 401 if no token provided.

	Anonymous users are returned with ``UserRole.ANONYMOUS``. Authenticated
	users are upgraded to ``UserRole.PAID`` if they have an active paid
	subscription, otherwise ``UserRole.FREE``.
	"""
	if credentials is None:
		raise HTTPException(status_code=401, detail='Authentication required.')
	payload = verify_supabase_jwt(credentials.credentials)
	user_id = get_user_id_from_payload(payload)
	if payload.get('is_anonymous', False):
		return AuthUser(user_id=UserId(user_id), role=UserRole.ANONYMOUS)
	role = await _resolve_role_from_subscription(user_id, sub_repo)
	return AuthUser(user_id=UserId(user_id), role=role)


async def get_required_auth_user(
	credentials: Annotated[
		HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))
	],
	sub_repo: Annotated[IUserSubscriptionRepository, Depends(get_user_subscription_repository)],
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
	role = await _resolve_role_from_subscription(user_id, sub_repo)
	return AuthUser(user_id=UserId(user_id), role=role)


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


async def get_chat_thread_repository(
	session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IChatThreadRepository:
	return PostgresChatThreadRepository(session=session)


def get_sse_blog_post_unit_of_work() -> BlogPostUnitOfWork:
	return PostgresBlogPostUnitOfWork(session_factory=create_async_session_factory())


def get_figure_storage_repository() -> IFigureStorageRepository:
	return SupabaseFigureStorageRepository()


def get_figure_chunk_repository() -> IFigureChunkRepository:
	return QdrantFigureChunkRepository()


def get_text_chunk_repository() -> ITextChunkRepository:
	return QdrantTextChunkRepository()


def get_usage_repository() -> IUsageRepository:
	return RoleBasedUsageRepository()


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


def get_figure_query_generator() -> IFigureQueryGenerator:
	return GeminiFigureQueryGenerator()


def get_suggest_figures_use_case(
	query_generator: Annotated[IFigureQueryGenerator, Depends(get_figure_query_generator)],
	query_embedding: Annotated[IQueryEmbeddingGateway, Depends(get_query_embedding_gateway)],
	figure_chunk_repository: Annotated[
		IFigureChunkRepository, Depends(get_figure_chunk_repository)
	],
	blog_post_repository: Annotated[IBlogPostRepository, Depends(get_blog_post_repository)],
) -> SuggestFiguresUseCase:
	return SuggestFiguresUseCase(
		query_generator=query_generator,
		query_embedding=query_embedding,
		figure_chunk_repository=figure_chunk_repository,
		blog_post_repository=blog_post_repository,
	)


# --------------------------------------
# Gateway providers
# --------------------------------------
def get_arxiv_source_fetcher() -> IArxivSourceFetcher:
	return ArxivSourceFetcher()


def get_tex_translation_gateway() -> ITexTranslationGateway:
	return HttpTexTranslationGateway()


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


def get_translate_arxiv_paper(
	tex_translation_gateway: Annotated[
		ITexTranslationGateway, Depends(get_tex_translation_gateway)
	],
) -> TranslateArxivPaper:
	return TranslateArxivPaper(tex_translation_gateway=tex_translation_gateway)


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


# --------------------------------------
# Chat use case providers
# --------------------------------------
def get_gemini_chat_llm() -> IChatLLMGateway:
	return GeminiChatLLM()


def get_chat_thread_unit_of_work() -> ChatThreadUnitOfWork:
	return PostgresChatThreadUnitOfWork(session_factory=create_async_session_factory())


def get_chat_with_paper_use_case(
	llm: Annotated[IChatLLMGateway, Depends(get_gemini_chat_llm)],
	thread_uow: Annotated[ChatThreadUnitOfWork, Depends(get_chat_thread_unit_of_work)],
	rag_text: Annotated[RagSearchTextUseCase, Depends(get_rag_search_text_use_case)],
	rag_image: Annotated[RagSearchImageUseCase, Depends(get_rag_search_image_use_case)],
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
) -> ChatWithPaperUseCase:
	return ChatWithPaperUseCase(
		llm=llm,
		thread_uow=thread_uow,
		rag_text=rag_text,
		rag_image=rag_image,
		usage_repository=usage_repository,
	)


def get_list_chat_threads_use_case(
	chat_thread_repository: Annotated[IChatThreadRepository, Depends(get_chat_thread_repository)],
) -> ListChatThreadsUseCase:
	return ListChatThreadsUseCase(chat_thread_repository=chat_thread_repository)


def get_get_chat_thread_use_case(
	chat_thread_repository: Annotated[IChatThreadRepository, Depends(get_chat_thread_repository)],
) -> GetChatThreadUseCase:
	return GetChatThreadUseCase(chat_thread_repository=chat_thread_repository)


def get_delete_chat_thread_use_case(
	thread_uow: Annotated[ChatThreadUnitOfWork, Depends(get_chat_thread_unit_of_work)],
) -> DeleteChatThreadUseCase:
	return DeleteChatThreadUseCase(thread_uow=thread_uow)


def get_get_my_chat_daily_count_use_case(
	chat_thread_repository: Annotated[IChatThreadRepository, Depends(get_chat_thread_repository)],
	usage_repository: Annotated[IUsageRepository, Depends(get_usage_repository)],
) -> GetMyChatDailyCountUseCase:
	return GetMyChatDailyCountUseCase(
		chat_thread_repository=chat_thread_repository,
		usage_repository=usage_repository,
	)


# --------------------------------------
# Billing (Stripe) providers
# --------------------------------------
def get_billing_gateway(
	config: Annotated[StripeConfig, Depends(get_stripe_config)],
) -> IBillingGateway:
	return StripeBillingGateway(config=config)


def get_get_my_subscription_use_case(
	repo: Annotated[IUserSubscriptionRepository, Depends(get_user_subscription_repository)],
) -> GetMySubscriptionUseCase:
	return GetMySubscriptionUseCase(repo=repo)


def get_start_checkout_use_case(
	billing: Annotated[IBillingGateway, Depends(get_billing_gateway)],
	repo: Annotated[IUserSubscriptionRepository, Depends(get_user_subscription_repository)],
) -> StartCheckoutUseCase:
	return StartCheckoutUseCase(billing=billing, repo=repo)


def get_start_customer_portal_use_case(
	billing: Annotated[IBillingGateway, Depends(get_billing_gateway)],
	repo: Annotated[IUserSubscriptionRepository, Depends(get_user_subscription_repository)],
) -> StartCustomerPortalUseCase:
	return StartCustomerPortalUseCase(billing=billing, repo=repo)


def get_handle_stripe_webhook_use_case(
	billing: Annotated[IBillingGateway, Depends(get_billing_gateway)],
	repo: Annotated[IUserSubscriptionRepository, Depends(get_user_subscription_repository)],
) -> HandleStripeWebhookUseCase:
	return HandleStripeWebhookUseCase(billing=billing, repo=repo)
