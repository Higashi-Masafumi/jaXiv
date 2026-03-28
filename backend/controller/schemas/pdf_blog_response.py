from datetime import datetime

from pydantic import BaseModel


class PdfBlogPostResponseSchema(BaseModel):
	paper_id: str
	content: str
	created_at: datetime
	updated_at: datetime
