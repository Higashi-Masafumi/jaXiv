from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from application.usecase.list_blog_posts import PaginatedBlogPosts
from domain.entities.blog import BlogPost


class BlogPostResponseSchema(BaseModel):
	paper_id: str
	title: str
	summary: str
	authors: list[str]
	source_url: str | None
	content: str
	created_at: datetime
	updated_at: datetime

	@classmethod
	def from_entity(cls, blog_post: BlogPost) -> BlogPostResponseSchema:
		return cls(
			paper_id=blog_post.paper_id,
			title=blog_post.title,
			summary=blog_post.summary,
			authors=blog_post.authors,
			source_url=blog_post.source_url,
			content=blog_post.content,
			created_at=blog_post.created_at,
			updated_at=blog_post.updated_at,
		)


class PaginatedBlogPostResponseSchema(BaseModel):
	items: list[BlogPostResponseSchema]
	total: int
	page: int
	page_size: int
	total_pages: int

	@classmethod
	def from_paginated(cls, paginated: PaginatedBlogPosts) -> PaginatedBlogPostResponseSchema:
		return cls(
			items=[BlogPostResponseSchema.from_entity(post) for post in paginated.items],
			total=paginated.total,
			page=paginated.page,
			page_size=paginated.page_size,
			total_pages=paginated.total_pages,
		)
