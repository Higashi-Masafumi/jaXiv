import shutil
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as PathParam
from fastapi import Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from controller.schemas import ErrorResponse
from dependencies import get_translate_arxiv_paper_use_case
from domain.errors import (
    ArxivPaperNotFoundError,
    LatexCompilationError,
    LatexCompilationTimeoutError,
    PdfNotGeneratedError,
    TexFileNotFoundError,
    TranslationEmptyResultError,
    TranslationFailedError,
)
from domain.value_objects import ArxivPaperId, TargetLanguage
from domain.value_objects.arxiv_paper_id import InvalidArxivPaperIdError
from usecase import TranslateArxivPaperUseCase

router = APIRouter(prefix="/api/v1/translate")


@router.post(
    "/arxiv/{arxiv_paper_id}",
    response_class=FileResponse,
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def translate_arxiv(
    arxiv_paper_id: Annotated[str, PathParam(description="arXiv paper ID")],
    target_language: Annotated[
        TargetLanguage, Query(description="Target language for translation")
    ],
    use_case: Annotated[
        TranslateArxivPaperUseCase, Depends(get_translate_arxiv_paper_use_case)
    ],
) -> FileResponse:
    """Translate and compile an arXiv paper, returning the resulting PDF as binary."""
    try:
        paper_id = ArxivPaperId(arxiv_paper_id)
    except InvalidArxivPaperIdError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    output_dir = tempfile.mkdtemp(prefix="tex-translation-")

    try:
        pdf_path = await use_case.execute(
            arxiv_paper_id=paper_id,
            target_language=target_language,
            output_dir=output_dir,
        )
    except InvalidArxivPaperIdError as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (ArxivPaperNotFoundError, TexFileNotFoundError) as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LatexCompilationTimeoutError as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=504, detail=str(e)) from e
    except (
        LatexCompilationError,
        PdfNotGeneratedError,
        TranslationEmptyResultError,
        TranslationFailedError,
    ) as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e)) from e

    filename = f"{paper_id.root}_translated.pdf"
    cleanup = BackgroundTask(shutil.rmtree, output_dir, ignore_errors=True)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        background=cleanup,
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
