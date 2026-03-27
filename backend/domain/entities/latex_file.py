from pydantic import BaseModel, ConfigDict, Field, StrictStr


class LatexFile(BaseModel):
	"""A latex file with its path and content."""

	model_config = ConfigDict(frozen=True)

	path: StrictStr = Field(description='The path of the latex file')
	content: StrictStr = Field(description='The content of the latex file')


class TranslatedLatexFile(BaseModel):
	"""A translated latex file reference for storage."""

	model_config = ConfigDict(frozen=True)

	path: StrictStr = Field(description='The local path of the translated pdf file')
	storage_path: StrictStr = Field(description='The path of the translated file in the storage')
