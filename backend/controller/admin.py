from typing import Annotated

from fastapi import APIRouter, Depends, Path

from application.usecase import GenerateBlogPostUseCase, SendWeeklyDigestsUseCase
from controller.blog import _get_output_dir
from controller.schemas.blog_response import BlogPostResponseSchema
from controller.schemas.subscription import DigestRunResultResponse
from domain.entities.auth_user import AuthUser
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from infrastructure.dependencies import (
	get_generate_blog_post,
	get_send_weekly_digests_use_case,
	get_system_auth_user,
	verify_job_admin_token,
)

# All routes here are for automated jobs, protected once at the router level by the
# JOB_ADMIN_TOKEN bearer token. Paths keep their original prefixes.
router = APIRouter(dependencies=[Depends(verify_job_admin_token)])


@router.post('/api/v1/blog/admin/arxiv/{arxiv_paper_id}', response_model=BlogPostResponseSchema)
async def generate_blog_admin(
	arxiv_paper_id: Annotated[str, Path(description='The arXiv paper ID')],
	generate_blog_post: Annotated[GenerateBlogPostUseCase, Depends(get_generate_blog_post)],
	auth_user: Annotated[AuthUser, Depends(get_system_auth_user)],
) -> BlogPostResponseSchema:
	"""Generate and publish a blog post from an arXiv paper as the system user.

	Intended for automated jobs (e.g. a local Claude tool selecting trending papers).
	Exempt from per-user monthly generation limits. Idempotent: returns the cached
	post if it already exists.
	"""
	blog_post = await generate_blog_post.execute(
		arxiv_paper_id=ArxivPaperId(arxiv_paper_id),
		output_dir=_get_output_dir(),
		auth_user=auth_user,
	)
	return BlogPostResponseSchema.from_entity(blog_post)


@router.post(
	'/api/v1/subscriptions/internal/send-weekly-digests',
	response_model=DigestRunResultResponse,
)
async def send_weekly_digests(
	use_case: Annotated[SendWeeklyDigestsUseCase, Depends(get_send_weekly_digests_use_case)],
) -> DigestRunResultResponse:
	"""Send the weekly digest to all active subscribers."""
	result = await use_case.execute()
	return DigestRunResultResponse.from_result(result)
