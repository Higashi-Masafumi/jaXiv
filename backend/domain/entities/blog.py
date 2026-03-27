import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BlogPost(BaseModel):
	id: uuid.UUID = Field(default_factory=uuid.uuid4)
	paper_id: str = Field(description='The arXiv paper ID')
	content: str = Field(description='The blog post content in Markdown')
	created_at: datetime = Field(description='The creation time')
	updated_at: datetime = Field(description='The last update time')
