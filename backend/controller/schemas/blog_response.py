from datetime import datetime

from pydantic import BaseModel


class BlogPostResponseSchema(BaseModel):
	paper_id: str
	title: str
	summary: str
	authors: list[str]
	source_url: str | None
	content: str
	created_at: datetime
	updated_at: datetime
