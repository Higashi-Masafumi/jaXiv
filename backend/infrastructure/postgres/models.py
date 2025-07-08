from sqlmodel import SQLModel, Field, UUID
import uuid
from datetime import datetime


class ArxivPaperMetadataWithTranslatedUrlModel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    paper_id: str = Field(index=True, unique=True)
    title: str = Field(description="The title of the paper")
    summary: str = Field(description="The summary of the paper")
    published_date: datetime = Field(description="The date the paper was published")
    authors: list[str] = Field(description="The authors of the paper")
    source_url: str = Field(description="The URL of the paper")
    translated_file_storage_path: str = Field(
        description="The path of the translated file in the storage"
    )
    translated_url: str = Field(description="The URL of the translated paper")
