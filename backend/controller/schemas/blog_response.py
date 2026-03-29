from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

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
