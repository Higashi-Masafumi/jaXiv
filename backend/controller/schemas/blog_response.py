from datetime import datetime

from pydantic import BaseModel


class BlogPostResponseSchema(BaseModel):
	paper_id: str
	content: str
	title: str
	summary: str
	authors: list[str]
	source_url: str
	created_at: datetime
	updated_at: datetime
