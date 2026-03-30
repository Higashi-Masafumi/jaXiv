import base64
import tempfile
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile

from controller.schemas import ExtractFiguresResponse, FigureResponse
from domain.errors.extraction_error import FigureExtractionError
from usecase.extract_figures import ExtractFiguresUseCase

router = APIRouter()


@router.post("/extract-figures", response_model=ExtractFiguresResponse)
def extract_figures(file: UploadFile, request: Request) -> ExtractFiguresResponse:
    use_case: ExtractFiguresUseCase = request.app.state.extract_figures_use_case

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
def health(request: Request) -> dict[str, str]:
    if not hasattr(request.app.state, "extract_figures_use_case"):
        return {"status": "not_ready"}
    return {"status": "ok"}
