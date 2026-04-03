import base64
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import HttpUrl

from controller.schemas import (
    AnalyzeChunksResponse,
    AnalyzeFiguresResponse,
    EmbedImagesRequest,
    EmbedImagesResponse,
    EmbedImageItemResponse,
    ExtractFiguresResponse,
    FigureResponse,
    FigureWithEmbeddingsResponse,
    TextChunkResponse,
)
from dependencies import (
    get_chunk_and_embed_use_case,
    get_embed_images_use_case,
    get_extract_figures_use_case,
    get_extract_figures_with_embeddings_use_case,
)
from domain.errors.extraction_error import FigureExtractionError
from libs.pdf_download import pdf_temp_path_from_url
from usecase.chunk_and_embed import ChunkAndEmbedUseCase
from usecase.embed_images import EmbedImagesIn, EmbedImagesInItem, EmbedImagesUseCase
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


@router.post("/extract-figures/by-url", response_model=ExtractFiguresResponse)
def extract_figures_by_url(
    pdf_url: HttpUrl,
    use_case: ExtractFiguresUseCase = Depends(get_extract_figures_use_case),
) -> ExtractFiguresResponse:
    try:
        with pdf_temp_path_from_url(str(pdf_url)) as pdf_path:
            try:
                figures = use_case.execute(pdf_path)
            except FigureExtractionError:
                raise
            except Exception as e:
                raise FigureExtractionError(
                    f"Unexpected error during extraction: {e}"
                ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

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
    use_case: ExtractFiguresWithEmbeddingsUseCase = Depends(
        get_extract_figures_with_embeddings_use_case
    ),
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
                caption_embeddings=fig.caption_embeddings.root,
            )
            for fig in figures
        ]
    )


@router.post("/analyze/figures/by-url", response_model=AnalyzeFiguresResponse)
def analyze_figures_by_url(
    pdf_url: HttpUrl,
    use_case: ExtractFiguresWithEmbeddingsUseCase = Depends(
        get_extract_figures_with_embeddings_use_case
    ),
) -> AnalyzeFiguresResponse:
    try:
        with pdf_temp_path_from_url(str(pdf_url)) as pdf_path:
            try:
                figures = use_case.execute(pdf_path)
            except FigureExtractionError:
                raise
            except Exception as e:
                raise FigureExtractionError(
                    f"Unexpected error during figure analysis: {e}"
                ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return AnalyzeFiguresResponse(
        figures=[
            FigureWithEmbeddingsResponse(
                image_base64=base64.b64encode(fig.image_bytes).decode(),
                caption=fig.caption,
                figure_number=fig.figure_number,
                page_number=fig.page_number,
                image_embeddings=fig.image_embeddings.root,
                caption_embeddings=fig.caption_embeddings.root,
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


@router.post("/analyze/chunks/by-url", response_model=AnalyzeChunksResponse)
def analyze_chunks_by_url(
    pdf_url: HttpUrl,
    use_case: ChunkAndEmbedUseCase = Depends(get_chunk_and_embed_use_case),
) -> AnalyzeChunksResponse:
    try:
        with pdf_temp_path_from_url(str(pdf_url)) as pdf_path:
            chunks = use_case.execute(pdf_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

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


@router.post("/embed/images", response_model=EmbedImagesResponse)
def embed_images(
    body: EmbedImagesRequest,
    use_case: EmbedImagesUseCase = Depends(get_embed_images_use_case),
) -> EmbedImagesResponse:
    """Embed images (+ captions) only; same Nomic models as ``/analyze/figures``."""
    try:
        out = use_case.execute(
            EmbedImagesIn(
                items=[
                    EmbedImagesInItem(image_base64=i.image_base64, caption=i.caption)
                    for i in body.items
                ]
            )
        )
        return EmbedImagesResponse(
            items=[
                EmbedImageItemResponse(
                    image_embeddings=i.image_embeddings,
                    caption_embeddings=i.caption_embeddings,
                )
                for i in out.items
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
