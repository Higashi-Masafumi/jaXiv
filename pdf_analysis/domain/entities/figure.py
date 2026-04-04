from pydantic import BaseModel, ConfigDict

from domain.entities.embedding import Embedding


class ExtractedFigure(BaseModel):
    """A figure extracted from a PDF with its caption and image bytes."""

    model_config = ConfigDict(frozen=True)

    image_bytes: bytes
    caption: str
    figure_number: int | None
    page_number: int


class ExtractedFigureWithEmbeddings(ExtractedFigure):
    """A figure extracted from a PDF with image embeddings and caption embeddings."""

    image_embeddings: Embedding
    caption_embeddings: Embedding
