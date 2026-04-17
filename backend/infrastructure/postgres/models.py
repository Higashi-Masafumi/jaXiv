import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import ARRAY, Column, Field, SQLModel, String


class ArxivPaperMetadataWithTranslatedUrlModel(SQLModel, table=True):
	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
	paper_id: str = Field(index=True, unique=True)
	title: str = Field(description='The title of the paper')
	summary: str = Field(description='The summary of the paper')
	published_date: datetime = Field(
		sa_column=Column(DateTime(timezone=True)),
		description='The date the paper was published',
	)
	authors: list[str] = Field(
		sa_column=Column(ARRAY(String)),
		description='The authors of the paper',
	)
	source_url: str = Field(description='The URL of the paper')
	translated_file_storage_path: str = Field(
		description='The path of the translated file in the storage'
	)
	translated_url: str = Field(description='The URL of the translated paper')


class BlogPostContentModel(SQLModel, table=True):
	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
	paper_id: str = Field(index=True, unique=True, description='The paper ID')
	title: str = Field(
		sa_column=Column(Text, nullable=False, server_default=''), description='Title of the paper'
	)
	summary: str = Field(
		sa_column=Column(Text, nullable=False, server_default=''), description='Abstract or summary'
	)
	authors: list[str] = Field(
		sa_column=Column(ARRAY(String), nullable=False, server_default='{}'),
		description='Author names',
	)
	source_url: str | None = Field(
		sa_column=Column(Text, nullable=True),
		default=None,
		description='URL of the original paper',
	)
	content: str = Field(sa_column=Column(Text), description='Blog post content in Markdown')
	source_type: str = Field(
		sa_column=Column(String(10), nullable=False, server_default='arxiv'),
		default='arxiv',
		description="Source type: 'arxiv' or 'pdf'",
	)
	user_id: uuid.UUID | None = Field(
		sa_column=Column(PG_UUID(as_uuid=True), nullable=True),
		default=None,
		description='Supabase user ID (anon or real)',
	)
	created_at: datetime = Field(
		sa_column=Column(DateTime(timezone=True)),
		description='The creation time',
	)
	updated_at: datetime = Field(
		sa_column=Column(DateTime(timezone=True)),
		description='The last update time',
	)
