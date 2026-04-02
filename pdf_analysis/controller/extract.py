import base64
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from controller.schemas import ExtractFiguresResponse, FigureResponse
from dependencies import get_extract_figures_use_case
from domain.errors.extraction_error import FigureExtractionError
from usecase.extract_figures import ExtractFiguresUseCase

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


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
