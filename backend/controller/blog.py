import os
import tempfile
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile

from controller.schemas.blog_response import BlogPostResponseSchema
from domain.value_objects import ArxivPaperId
from infrastructure.dependencies import (
	get_generate_blog_post,
	get_generate_blog_post_from_pdf,
	get_get_blog_post,
	get_list_blog_posts,
)
from usecase import GenerateBlogPostFromPdfUseCase, GenerateBlogPostUseCase, GetBlogPostUseCase, ListBlogPostsUseCase

router = APIRouter(prefix='/api/v1/blog')


def _get_output_dir() -> str:
	output_dir = os.getenv('OUTPUT_DIR', './output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	return output_dir


@router.get('/', response_model=list[BlogPostResponseSchema])
async def list_blogs(
	list_blog_posts: Annotated[ListBlogPostsUseCase, Depends(get_list_blog_posts)],
) -> list[BlogPostResponseSchema]:
	blog_posts = await list_blog_posts.execute()
	return [BlogPostResponseSchema.from_entity(post) for post in blog_posts]


@router.post('/arxiv/{arxiv_paper_id}', response_model=BlogPostResponseSchema)
async def generate_blog(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	generate_blog_post: Annotated[GenerateBlogPostUseCase, Depends(get_generate_blog_post)],
) -> BlogPostResponseSchema:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(arxiv_paper_id)
	blog_post = await generate_blog_post.execute(arxiv_paper_id=paper_id, output_dir=output_dir)
	return BlogPostResponseSchema.from_entity(blog_post)


@router.get('/{paper_id}', response_model=BlogPostResponseSchema)
async def get_blog(
	paper_id: Annotated[str, Path(description='The paper ID')],
	get_blog_post: Annotated[GetBlogPostUseCase, Depends(get_get_blog_post)],
) -> BlogPostResponseSchema:
	blog_post = await get_blog_post.execute(paper_id=paper_id)
	if blog_post is None:
		raise HTTPException(status_code=404, detail=f'Blog post for {paper_id} not found.')
	return BlogPostResponseSchema.from_entity(blog_post)


@router.post('/pdf', response_model=BlogPostResponseSchema)
async def generate_blog_from_pdf(
	file: Annotated[UploadFile, File(description='PDF file of the paper')],
	generate_blog_post_from_pdf: Annotated[
		GenerateBlogPostFromPdfUseCase, Depends(get_generate_blog_post_from_pdf)
	],
) -> BlogPostResponseSchema:
	if not file.filename or not file.filename.lower().endswith('.pdf'):
		raise HTTPException(status_code=400, detail='Uploaded file must be a PDF.')

	tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
	pdf_path = FilePath(tmp.name)
	try:
		content = await file.read()
		tmp.write(content)
		tmp.close()

		blog_post = await generate_blog_post_from_pdf.execute(pdf_path=pdf_path)
		return BlogPostResponseSchema.from_entity(blog_post)
	finally:
		pdf_path.unlink(missing_ok=True)
