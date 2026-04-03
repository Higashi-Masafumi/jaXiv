from pydantic import BaseModel, ConfigDict

from domain.value_objects.embedding import Embedding


class ExtractedFigure(BaseModel):
	"""A figure extracted from a PDF (without embeddings)."""

	model_config = ConfigDict(frozen=True)

	image_bytes: bytes
	caption: str
	figure_number: int | None
	page_number: int


class FigureWithEmbedding(BaseModel):
	"""A figure extracted from a PDF with image and caption embeddings."""

	model_config = ConfigDict(frozen=True)

	image_bytes: bytes
	caption: str
	figure_number: int | None
	page_number: int
	image_embeddings: Embedding
	caption_embeddings: Embedding


class UploadedFigure(BaseModel):
	"""A figure that has been uploaded to storage with a public URL."""

	model_config = ConfigDict(frozen=True)

	url: str
	caption: str
	figure_number: int | None
	page_number: int
