import base64
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from controller.schemas import (
    AnalyzeChunksResponse,
    AnalyzeFiguresResponse,
    ExtractFiguresResponse,
    FigureResponse,
    FigureWithEmbeddingsResponse,
    TextChunkResponse,
)
from dependencies import (
    get_chunk_and_embed_use_case,
    get_extract_figures_use_case,
    get_extract_figures_with_embeddings_use_case,
)
from domain.errors.extraction_error import FigureExtractionError
from usecase.chunk_and_embed import ChunkAndEmbedUseCase
from usecase.extract_figures import ExtractFiguresUseCase
from usecase.extract_figures_with_embeddings import ExtractFiguresWithEmbeddingsUseCase

router = APIRouter()


@router.post("/extract-figures", response_model=ExtractFiguresResponse)
def extract_figures(
    file: UploadFile,
    use_case: ExtractFiguresUseCase = Depends(get_extract_figures_use_case),
) -> ExtractFiguresResponse:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        pdf_path = Path(tmp.name)

        try:
            figures = use_case.execute(pdf_path)
        except FigureExtractionError:
            raise
        except Exception as e:
            raise FigureExtractionError(
                f"Unexpected error during extraction: {e}"
            ) from e

    return ExtractFiguresResponse(
        figures=[
            FigureResponse(
                image_base64=base64.b64encode(fig.image_bytes).decode(),
                caption=fig.caption,
                figure_number=fig.figure_number,
                page_number=fig.page_number,
            )
            for fig in figures
        ]
    )


@router.post("/analyze/figures", response_model=AnalyzeFiguresResponse)
def analyze_figures(
    file: UploadFile,
    use_case: ExtractFiguresWithEmbeddingsUseCase = Depends(get_extract_figures_with_embeddings_use_case),
) -> AnalyzeFiguresResponse:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        pdf_path = Path(tmp.name)

        try:
            figures = use_case.execute(pdf_path)
        except FigureExtractionError:
            raise
        except Exception as e:
            raise FigureExtractionError(
                f"Unexpected error during figure analysis: {e}"
            ) from e

    return AnalyzeFiguresResponse(
        figures=[
            FigureWithEmbeddingsResponse(
                image_base64=base64.b64encode(fig.image_bytes).decode(),
                caption=fig.caption,
                figure_number=fig.figure_number,
                page_number=fig.page_number,
                image_embeddings=fig.image_embeddings.root,
            )
            for fig in figures
        ]
    )


@router.post("/analyze/chunks", response_model=AnalyzeChunksResponse)
def analyze_chunks(
    file: UploadFile,
    use_case: ChunkAndEmbedUseCase = Depends(get_chunk_and_embed_use_case),
) -> AnalyzeChunksResponse:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        pdf_path = Path(tmp.name)
        chunks = use_case.execute(pdf_path)

    return AnalyzeChunksResponse(
        chunks=[
            TextChunkResponse(
                text=chunk.text,
                page_number=chunk.page_number,
                text_embeddings=chunk.text_embeddings.root,
            )
            for chunk in chunks
        ]
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
