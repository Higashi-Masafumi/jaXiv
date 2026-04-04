from pydantic import BaseModel, ConfigDict, StrictStr

from domain.value_objects.embedding import Embedding


class TextChunkWithEmbedding(BaseModel):
	"""A text chunk extracted from a PDF with its embedding."""

	model_config = ConfigDict(frozen=True)
	text: StrictStr
	page_number: int
	embeddings: Embedding
