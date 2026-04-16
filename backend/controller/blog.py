import os
import tempfile
import uuid
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from sse_starlette import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from domain.value_objects.user_id import UserId

from application.usecase import (
	GenerateBlogPostFromPdfSSEUseCase,
	GenerateBlogPostFromPdfUseCase,
	GenerateBlogPostSSEUseCase,
	GenerateBlogPostUseCase,
	GetBlogPostUseCase,
	ListBlogPostsUseCase,
	ListMyBlogPostsUseCase,
	RagSearchImageUseCase,
	RagSearchTextUseCase,
)
from controller.schemas.blog_response import BlogPostResponseSchema, PaginatedBlogPostResponseSchema
from controller.schemas.rag_response import (
	RagSearchImageResponseSchema,
	RagSearchRequestSchema,
	RagSearchTextResponseSchema,
)
from domain.errors.domain_error import PdfProcessingError
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.blog_paper_id import InvalidBlogPaperIdError
from infrastructure.dependencies import (
	get_generate_blog_post,
	get_generate_blog_post_from_pdf,
	get_get_blog_post,
	get_list_blog_posts,
	get_list_my_blog_posts,
	get_optional_user_id,
	get_rag_search_image_use_case,
	get_rag_search_text_use_case,
	get_required_user_id,
	get_sse_generate_blog_post,
	get_sse_generate_blog_post_from_pdf,
)

router = APIRouter(prefix='/api/v1/blog')


def _get_output_dir() -> str:
	output_dir = os.getenv('OUTPUT_DIR', './output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	return output_dir


@router.get('/', response_model=PaginatedBlogPostResponseSchema)
async def list_blogs(
	list_blog_posts: Annotated[ListBlogPostsUseCase, Depends(get_list_blog_posts)],
	page: Annotated[int, Query(ge=1, description='Page number')] = 1,
	page_size: Annotated[int, Query(ge=1, le=100, description='Items per page')] = 10,
) -> PaginatedBlogPostResponseSchema:
	paginated = await list_blog_posts.execute(page=page, page_size=page_size)
	return PaginatedBlogPostResponseSchema.from_paginated(paginated)


@router.get('/my', response_model=PaginatedBlogPostResponseSchema)
async def list_my_blogs(
	user_id: Annotated[uuid.UUID, Depends(get_required_user_id)],
	list_my_blog_posts: Annotated[ListMyBlogPostsUseCase, Depends(get_list_my_blog_posts)],
	page: Annotated[int, Query(ge=1, description='Page number')] = 1,
	page_size: Annotated[int, Query(ge=1, le=100, description='Items per page')] = 10,
) -> PaginatedBlogPostResponseSchema:
	paginated = await list_my_blog_posts.execute(
		user_id=UserId(user_id), page=page, page_size=page_size
	)
	return PaginatedBlogPostResponseSchema.from_paginated(paginated)


@router.post('/arxiv/{arxiv_paper_id}', response_model=BlogPostResponseSchema)
async def generate_blog(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	generate_blog_post: Annotated[GenerateBlogPostUseCase, Depends(get_generate_blog_post)],
	user_id: Annotated[uuid.UUID | None, Depends(get_optional_user_id)] = None,
) -> BlogPostResponseSchema:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(arxiv_paper_id)
	try:
		blog_post = await generate_blog_post.execute(
			arxiv_paper_id=paper_id,
			output_dir=output_dir,
			user_id=UserId(user_id) if user_id else None,
		)
		return BlogPostResponseSchema.from_entity(blog_post)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e)) from e


@router.get('/arxiv/{arxiv_paper_id}/stream', response_class=EventSourceResponse)
async def generate_blog_stream(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	generate_blog_post: Annotated[GenerateBlogPostSSEUseCase, Depends(get_sse_generate_blog_post)],
	user_id: Annotated[uuid.UUID | None, Depends(get_optional_user_id)] = None,
) -> EventSourceResponse:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(arxiv_paper_id)

	async def run_workflow():
		iterator = generate_blog_post.execute(
			arxiv_paper_id=paper_id,
			output_dir=output_dir,
			user_id=UserId(user_id) if user_id else None,
		)
		async for chunk in iterator:
			if chunk.type == 'intermediate':
				yield ServerSentEvent(data=chunk.to_json_string())
			elif chunk.type == 'complete':
				yield ServerSentEvent(data=chunk.to_json_string())
				return
			elif chunk.type == 'error':
				yield ServerSentEvent(data=chunk.to_json_string())
				return

	return EventSourceResponse(run_workflow(), ping=10)


@router.post('/{paper_id}/rag/text', response_model=RagSearchTextResponseSchema)
async def rag_search_text(
	paper_id: Annotated[str, Path(description='The paper ID')],
	body: RagSearchRequestSchema,
	use_case: Annotated[RagSearchTextUseCase, Depends(get_rag_search_text_use_case)],
) -> RagSearchTextResponseSchema:
	try:
		result = await use_case.execute(
			paper_id=paper_id,
			query=body.query,
			limit=body.limit,
		)
		return RagSearchTextResponseSchema.from_result(result)
	except InvalidBlogPaperIdError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e
	except PdfProcessingError as e:
		raise HTTPException(status_code=502, detail=str(e)) from e


@router.post('/{paper_id}/rag/image', response_model=RagSearchImageResponseSchema)
async def rag_search_image(
	paper_id: Annotated[str, Path(description='The paper ID')],
	body: RagSearchRequestSchema,
	use_case: Annotated[RagSearchImageUseCase, Depends(get_rag_search_image_use_case)],
) -> RagSearchImageResponseSchema:
	try:
		result = await use_case.execute(
			paper_id=paper_id,
			query=body.query,
			limit=body.limit,
		)
		return RagSearchImageResponseSchema.from_result(result)
	except InvalidBlogPaperIdError as e:
		raise HTTPException(status_code=400, detail=str(e)) from e
	except PdfProcessingError as e:
		raise HTTPException(status_code=502, detail=str(e)) from e


@router.get('/{paper_id}', response_model=BlogPostResponseSchema)
async def get_blog(
	paper_id: Annotated[str, Path(description='The paper ID')],
	get_blog_post: Annotated[GetBlogPostUseCase, Depends(get_get_blog_post)],
	user_id: Annotated[uuid.UUID | None, Depends(get_optional_user_id)] = None,
) -> BlogPostResponseSchema:
	blog_post = await get_blog_post.execute(paper_id=paper_id)
	if blog_post is None:
		raise HTTPException(status_code=404, detail=f'Blog post for {paper_id} not found.')
	# PDF posts are private: only the owner can view them.
	# Return 404 (not 403) to avoid leaking the existence of private posts.
	if blog_post.source_type.is_pdf and blog_post.user_id != (UserId(user_id) if user_id else None):
		raise HTTPException(status_code=404, detail=f'Blog post for {paper_id} not found.')
	return BlogPostResponseSchema.from_entity(blog_post)


@router.post('/pdf', response_model=BlogPostResponseSchema)
async def generate_blog_from_pdf(
	file: Annotated[UploadFile, File(description='PDF file of the paper')],
	generate_blog_post_from_pdf: Annotated[
		GenerateBlogPostFromPdfUseCase, Depends(get_generate_blog_post_from_pdf)
	],
	user_id: Annotated[uuid.UUID, Depends(get_required_user_id)],
) -> BlogPostResponseSchema:
	if not file.filename or not file.filename.lower().endswith('.pdf'):
		raise HTTPException(status_code=400, detail='Uploaded file must be a PDF.')

	tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
	pdf_path = FilePath(tmp.name)
	try:
		content = await file.read()
		tmp.write(content)
		tmp.close()

		try:
			blog_post = await generate_blog_post_from_pdf.execute(
				pdf_path=pdf_path, user_id=UserId(user_id)
			)
			return BlogPostResponseSchema.from_entity(blog_post)
		except Exception as e:
			raise HTTPException(status_code=500, detail=str(e)) from e
	finally:
		pdf_path.unlink(missing_ok=True)


@router.post('/pdf/stream', response_class=EventSourceResponse)
async def generate_blog_from_pdf_stream(
	file: Annotated[UploadFile, File(description='PDF file of the paper')],
	generate_blog_post_from_pdf: Annotated[
		GenerateBlogPostFromPdfSSEUseCase, Depends(get_sse_generate_blog_post_from_pdf)
	],
	user_id: Annotated[uuid.UUID, Depends(get_required_user_id)],
) -> EventSourceResponse:
	if not file.filename or not file.filename.lower().endswith('.pdf'):
		raise HTTPException(status_code=400, detail='Uploaded file must be a PDF.')

	tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
	pdf_path = FilePath(tmp.name)
	content = await file.read()
	tmp.write(content)
	tmp.close()

	async def run_workflow():
		try:
			iterator = generate_blog_post_from_pdf.execute(
				pdf_path=pdf_path, user_id=UserId(user_id)
			)
			async for chunk in iterator:
				if chunk.type == 'intermediate':
					yield ServerSentEvent(data=chunk.to_json_string())
				elif chunk.type == 'complete':
					yield ServerSentEvent(data=chunk.to_json_string())
					return
				elif chunk.type == 'error':
					yield ServerSentEvent(data=chunk.to_json_string())
					return
		finally:
			pdf_path.unlink(missing_ok=True)

	return EventSourceResponse(run_workflow(), ping=10)
