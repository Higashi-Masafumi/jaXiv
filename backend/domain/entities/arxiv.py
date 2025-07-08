from pydantic import RootModel, BaseModel, Field, StrictStr, HttpUrl
from datetime import datetime


class ArxivPaperId(RootModel[str]):
    root: str


class ArxivPaperAuthor(BaseModel):
    name: StrictStr = Field(description="The name of the author")


class ArxivPaperMetadata(BaseModel):
    paper_id: ArxivPaperId = Field(description="The ID of the paper")
    title: StrictStr = Field(description="The title of the paper")
    summary: StrictStr = Field(description="The summary of the paper")
    published_date: datetime = Field(description="The date the paper was published")
    authors: list[ArxivPaperAuthor] = Field(description="The authors of the paper")
    source_url: HttpUrl = Field(description="The URL of the paper")


class ArxivPaperMetadataWithTranslatedUrl(ArxivPaperMetadata):
    translated_file_storage_path: StrictStr = Field(
        description="The path of the translated file in the storage"
    )
    translated_url: HttpUrl = Field(description="The URL of the translated paper")
