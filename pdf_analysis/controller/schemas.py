from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FigureResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_base64: str
    caption: str
    figure_number: int | None
    page_number: int


class ExtractFiguresResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    figures: list[FigureResponse]


class FigureWithEmbeddingsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_base64: str
    caption: str
    figure_number: int | None
    page_number: int
    image_embeddings: list[float]
    caption_embeddings: list[float]


class AnalyzeFiguresResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    figures: list[FigureWithEmbeddingsResponse]


class TextChunkResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    page_number: int
    text_embeddings: list[float]


class AnalyzeChunksResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunks: list[TextChunkResponse]


class EmbedImageItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_base64: str
    caption: str | None = None


class EmbedImagesRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[EmbedImageItemRequest]


class EmbedImageItemResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_embeddings: list[float]
    caption_embeddings: list[float]


class EmbedImagesResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[EmbedImageItemResponse]


class EmbedQueryRequest(BaseModel):
    """Single-text embedding for RAG query vectors (must match Qdrant index models)."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1)
    kind: Literal["bge", "nomic"]


class EmbedQueryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    embedding: list[float]
