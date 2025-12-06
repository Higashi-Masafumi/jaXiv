from pydantic import BaseModel, Field, StrictStr


class LatexFile(BaseModel):
	"""
	A latex file.
	"""

	path: StrictStr = Field(description='The path of the latex file')
	content: StrictStr = Field(description='The content of the latex file')


class TranslatedLatexFile(BaseModel):
	"""
	A translated latex file.
	"""

	path: StrictStr = Field(description='The path of the translated latex file')
	storage_path: StrictStr = Field(
		description='The path of the translated latex file in the storage'
	)
