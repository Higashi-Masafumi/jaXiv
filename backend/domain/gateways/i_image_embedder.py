from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, ConfigDict, StrictStr

from domain.value_objects.embedding import Embedding


class ImageEmbedItem(BaseModel):
	"""An image to embed, referenced by path so it is only read when it is sent."""

	model_config = ConfigDict(frozen=True)

	image_path: Path
	caption: StrictStr | None = None


class ImageWithEmbedding(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_embeddings: Embedding
	caption_embeddings: Embedding


class IImageEmbedder(ABC):
	"""Gateway for embedding raw images (+ optional captions) via the pdf_analysis service."""

	@abstractmethod
	async def embed_images(self, items: list[ImageEmbedItem]) -> list[ImageWithEmbedding]:
		"""Embed images using Nomic vision + text models. No PDF parsing involved.

		Returns one embedding per item, in the same order as ``items``.
		"""
		...
