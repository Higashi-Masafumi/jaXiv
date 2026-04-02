from pydantic import BaseModel, ConfigDict


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
