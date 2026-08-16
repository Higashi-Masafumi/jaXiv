from pathlib import Path

from pydantic import BaseModel, ConfigDict

from domain.value_objects.embedding import Embedding


class ExtractedFigure(BaseModel):
	"""A figure extracted from a PDF (without embeddings).

	The image is referenced by path rather than carried as bytes: a paper yields
	up to 20 figures, and holding all of them in memory at once is the main
	source of out-of-memory kills on small containers. The file lives in the
	directory the caller handed to the extractor and is only valid for as long as
	the caller keeps that directory around.
	"""

	model_config = ConfigDict(frozen=True)

	image_path: Path
	caption: str
	figure_number: int | None
	page_number: int


class FigureWithEmbedding(BaseModel):
	"""A figure extracted from a PDF with image and caption embeddings.

	``image_path`` follows the same ownership rule as ``ExtractedFigure``.
	"""

	model_config = ConfigDict(frozen=True)

	image_path: Path
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
