from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, StrictStr, field_validator

from domain.value_objects import ArxivPaperId


class ArxivPaperAuthor(BaseModel):
	name: StrictStr = Field(description='The name of the author')


class ArxivPaperMetadata(BaseModel):
	paper_id: ArxivPaperId = Field(description='The ID of the paper')
	title: StrictStr = Field(description='The title of the paper')
	summary: StrictStr = Field(description='The summary of the paper')
	published_date: datetime = Field(description='The date the paper was published')
	authors: list[ArxivPaperAuthor] = Field(description='The authors of the paper')
	source_url: HttpUrl = Field(description='The URL of the paper')

	@field_validator('published_date', mode='before')
	@classmethod
	def fix_invalid_published_date(cls, v) -> datetime:
		if isinstance(v, str):
			if v.endswith('+00'):
				v = v.replace('+00', '+00:00')
			try:
				return datetime.fromisoformat(v)
			except ValueError:
				return datetime.fromisoformat(v)
		return v

	def with_translated_url(
		self,
		translated_file_storage_path: str,
		translated_url: HttpUrl,
	) -> 'ArxivPaperMetadataWithTranslatedUrl':
		"""Create a new entity with translated URL information."""
		return ArxivPaperMetadataWithTranslatedUrl(
			**self.model_dump(),
			translated_file_storage_path=translated_file_storage_path,
			translated_url=translated_url,
		)


class ArxivPaperMetadataWithTranslatedUrl(ArxivPaperMetadata):
	translated_file_storage_path: StrictStr = Field(
		description='The path of the translated file in the storage'
	)
	translated_url: HttpUrl = Field(description='The URL of the translated paper')
