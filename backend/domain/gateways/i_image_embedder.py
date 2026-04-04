from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, StrictStr

from domain.value_objects.embedding import Embedding


class ImageEmbedItem(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_base64: StrictStr
	caption: StrictStr | None = None


class ImageWithEmbedding(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_embeddings: Embedding
	caption_embeddings: Embedding


class IImageEmbedder(ABC):
	"""Gateway for embedding raw images (+ optional captions) via the pdf_analysis service."""

	@abstractmethod
	async def embed_images(self, items: list[ImageEmbedItem]) -> list[ImageWithEmbedding]:
		"""Embed images using Nomic vision + text models. No PDF parsing involved."""
		...
