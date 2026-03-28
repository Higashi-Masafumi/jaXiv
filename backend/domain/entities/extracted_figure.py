from pydantic import BaseModel, ConfigDict


class ExtractedFigure(BaseModel):
	"""A figure extracted from a PDF with its caption and image bytes."""

	model_config = ConfigDict(frozen=True)

	image_bytes: bytes
	caption: str
	figure_number: int | None
	page_number: int


class UploadedFigure(BaseModel):
	"""A figure that has been uploaded to storage with a public URL."""

	model_config = ConfigDict(frozen=True)

	url: str
	caption: str
	figure_number: int | None
	page_number: int
