import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from controller.schemas.blog_response import BlogPostResponseSchema
from domain.value_objects import ArxivPaperId
from infrastructure.dependencies import get_generate_blog_post, get_get_blog_post
from usecase import GenerateBlogPostUsecase, GetBlogPostUsecase

router = APIRouter(prefix='/api/v1/blog')


def _get_output_dir() -> str:
	output_dir = os.getenv('OUTPUT_DIR', './output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	return output_dir


def _to_schema(result) -> BlogPostResponseSchema:
	return BlogPostResponseSchema(
		paper_id=result.blog_post.paper_id,
		content=result.blog_post.content,
		title=result.paper_metadata.title,
		summary=result.paper_metadata.summary,
		authors=[a.name for a in result.paper_metadata.authors],
		source_url=str(result.paper_metadata.source_url),
		created_at=result.blog_post.created_at,
		updated_at=result.blog_post.updated_at,
	)


@router.post('/arxiv/{arxiv_paper_id}', response_model=BlogPostResponseSchema)
async def generate_blog(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	generate_blog_post: Annotated[GenerateBlogPostUsecase, Depends(get_generate_blog_post)],
	get_blog_post: Annotated[GetBlogPostUsecase, Depends(get_get_blog_post)],
) -> BlogPostResponseSchema:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(value=arxiv_paper_id)
	await generate_blog_post.execute(arxiv_paper_id=paper_id, output_dir=output_dir)
	result = await get_blog_post.execute(arxiv_paper_id=paper_id)
	if result is None:
		raise HTTPException(status_code=500, detail='Blog post generation failed.')
	return _to_schema(result)


@router.get('/arxiv/{arxiv_paper_id}', response_model=BlogPostResponseSchema)
async def get_blog(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	get_blog_post: Annotated[GetBlogPostUsecase, Depends(get_get_blog_post)],
) -> BlogPostResponseSchema:
	paper_id = ArxivPaperId(value=arxiv_paper_id)
	result = await get_blog_post.execute(arxiv_paper_id=paper_id)
	if result is None:
		raise HTTPException(status_code=404, detail=f'Blog post for {arxiv_paper_id} not found.')
	return _to_schema(result)
