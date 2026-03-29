from pydantic import BaseModel, ConfigDict, Field


class PdfPaperMetadata(BaseModel):
	"""Metadata for a PDF paper uploaded by the user."""

	model_config = ConfigDict(frozen=True)

	title: str = Field(description='The title of the paper')
	authors: list[str] = Field(default_factory=list, description='Author names')
	summary: str = Field(default='', description='Optional abstract/summary')
