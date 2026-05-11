from pydantic import BaseModel, ConfigDict, Field, StrictStr


class TranslatedLatexFile(BaseModel):
	"""A translated latex file reference for storage."""

	model_config = ConfigDict(frozen=True)

	path: StrictStr = Field(description='The local path of the translated pdf file')
	storage_path: StrictStr = Field(description='The path of the translated file in the storage')
