import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BlogPost(BaseModel):
	id: uuid.UUID = Field(default_factory=uuid.uuid4)
	paper_id: str = Field(description='The paper ID')
	title: str = Field(default='', description='The title of the paper')
	summary: str = Field(default='', description='The abstract or summary of the paper')
	authors: list[str] = Field(default_factory=list, description='Author names')
	source_url: str | None = Field(default=None, description='URL of the original paper')
	content: str = Field(description='The blog post content in Markdown')
	created_at: datetime = Field(description='The creation time')
	updated_at: datetime = Field(description='The last update time')
