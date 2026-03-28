import os
import tempfile
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile

from controller.schemas.blog_response import BlogPostResponseSchema
from controller.schemas.pdf_blog_response import PdfBlogPostResponseSchema
from domain.gateways import IArxivSourceFetcher
from domain.value_objects import ArxivPaperId
from infrastructure.dependencies import (
	get_arxiv_source_fetcher,
	get_generate_blog_post,
	get_generate_blog_post_from_pdf,
	get_get_blog_post,
)
from usecase import GenerateBlogPostFromPdfUseCase, GenerateBlogPostUseCase, GetBlogPostUseCase

router = APIRouter(prefix='/api/v1/blog')


def _get_output_dir() -> str:
	output_dir = os.getenv('OUTPUT_DIR', './output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	return output_dir


@router.post('/arxiv/{arxiv_paper_id}', response_model=BlogPostResponseSchema)
async def generate_blog(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	generate_blog_post: Annotated[GenerateBlogPostUseCase, Depends(get_generate_blog_post)],
	arxiv_source_fetcher: Annotated[IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)],
) -> BlogPostResponseSchema:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(arxiv_paper_id)
	blog_post = await generate_blog_post.execute(arxiv_paper_id=paper_id, output_dir=output_dir)
	paper_metadata = arxiv_source_fetcher.fetch_paper_metadata(paper_id=paper_id)
	return BlogPostResponseSchema(
		paper_id=blog_post.paper_id,
		content=blog_post.content,
		title=paper_metadata.title,
		summary=paper_metadata.summary,
		authors=[a.name for a in paper_metadata.authors],
		source_url=str(paper_metadata.source_url),
		created_at=blog_post.created_at,
		updated_at=blog_post.updated_at,
	)


@router.get('/{paper_id}', response_model=PdfBlogPostResponseSchema)
async def get_blog(
	paper_id: Annotated[str, Path(description='The paper ID')],
	get_blog_post: Annotated[GetBlogPostUseCase, Depends(get_get_blog_post)],
) -> PdfBlogPostResponseSchema:
	blog_post = await get_blog_post.execute(paper_id=paper_id)
	if blog_post is None:
		raise HTTPException(status_code=404, detail=f'Blog post for {paper_id} not found.')
	return PdfBlogPostResponseSchema(
		paper_id=blog_post.paper_id,
		content=blog_post.content,
		created_at=blog_post.created_at,
		updated_at=blog_post.updated_at,
	)


@router.post('/pdf', response_model=PdfBlogPostResponseSchema)
async def generate_blog_from_pdf(
	file: Annotated[UploadFile, File(description='PDF file of the paper')],
	generate_blog_post_from_pdf: Annotated[
		GenerateBlogPostFromPdfUseCase, Depends(get_generate_blog_post_from_pdf)
	],
) -> PdfBlogPostResponseSchema:
	if not file.filename or not file.filename.lower().endswith('.pdf'):
		raise HTTPException(status_code=400, detail='Uploaded file must be a PDF.')

	tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
	pdf_path = FilePath(tmp.name)
	try:
		content = await file.read()
		tmp.write(content)
		tmp.close()

		blog_post = await generate_blog_post_from_pdf.execute(pdf_path=pdf_path)

		return PdfBlogPostResponseSchema(
			paper_id=blog_post.paper_id,
			content=blog_post.content,
			created_at=blog_post.created_at,
			updated_at=blog_post.updated_at,
		)
	finally:
		pdf_path.unlink(missing_ok=True)
