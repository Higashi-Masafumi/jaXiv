"""Embed pre-extracted images (+ optional captions) without PDF parsing."""

import base64
import binascii

from pydantic import BaseModel, ConfigDict

from domain.gateways.image_embedding import ImageEmbeddingGateway
from domain.gateways.text_embedding import TextEmbeddingGateway


class EmbedImagesInItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_base64: str
    caption: str | None = None


class EmbedImagesIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[EmbedImagesInItem]


class EmbedImagesOutItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_embeddings: list[float]
    caption_embeddings: list[float]


class EmbedImagesOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[EmbedImagesOutItem]


class EmbedImagesUseCase:
    """Vision + text embedding on raw image bytes (no PDF / ONNX pipeline)."""

    def __init__(
        self,
        image_embedding: ImageEmbeddingGateway,
        caption_embedding: TextEmbeddingGateway,
    ) -> None:
        self._image_embedding = image_embedding
        self._caption_embedding = caption_embedding

    def execute(self, inp: EmbedImagesIn) -> EmbedImagesOut:
        if not inp.items:
            return EmbedImagesOut(items=[])

        image_bytes_list: list[bytes] = []
        captions: list[str] = []
        for item in inp.items:
            try:
                image_bytes_list.append(base64.b64decode(item.image_base64))
            except binascii.Error as e:
                raise ValueError("Invalid base64 in image_base64") from e
            cap = (item.caption or "").strip()
            captions.append(cap if cap else "figure")

        image_embeddings = self._image_embedding.embed_image_batch(image_bytes_list)
        caption_embeddings = self._caption_embedding.embed_text_batch(captions)

        return EmbedImagesOut(
            items=[
                EmbedImagesOutItem(
                    image_embeddings=img.root,
                    caption_embeddings=cap.root,
                )
                for img, cap in zip(image_embeddings, caption_embeddings, strict=True)
            ]
        )
