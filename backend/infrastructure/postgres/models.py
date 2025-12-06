import uuid
from datetime import datetime

from sqlmodel import ARRAY, Column, Field, SQLModel, String


class ArxivPaperMetadataWithTranslatedUrlModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    paper_id: str = Field(index=True, unique=True)
    title: str = Field(description="The title of the paper")
    summary: str = Field(description="The summary of the paper")
    published_date: datetime = Field(description="The date the paper was published")
    authors: list[str] = Field(
        sa_column=Column(ARRAY(String)),
        description="The authors of the paper",
    )
    source_url: str = Field(description="The URL of the paper")
    translated_file_storage_path: str = Field(
        description="The path of the translated file in the storage"
    )
    translated_url: str = Field(description="The URL of the translated paper")
