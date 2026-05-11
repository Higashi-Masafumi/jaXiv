from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Path as PathParam
from fastapi import Query
from fastapi.responses import Response

from dependencies import get_translate_arxiv_paper_use_case
from domain.value_objects import ArxivPaperId, TargetLanguage
from usecase import TranslateArxivPaperUseCase

router = APIRouter(prefix="/api/v1/translate")


def _parse_arxiv_paper_id(
    arxiv_paper_id: Annotated[str, PathParam(description="arXiv paper ID")],
) -> ArxivPaperId:
    # ArxivPaperId raises InvalidArxivPaperIdError on invalid input, which the
    # ExceptionHandler middleware maps to a 400 response.
    return ArxivPaperId(arxiv_paper_id)


@router.post(
    "/arxiv/{arxiv_paper_id}",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def translate_arxiv(
    arxiv_paper_id: Annotated[ArxivPaperId, Depends(_parse_arxiv_paper_id)],
    target_language: Annotated[
        TargetLanguage, Query(description="Target language for translation")
    ],
    use_case: Annotated[
        TranslateArxivPaperUseCase, Depends(get_translate_arxiv_paper_use_case)
    ],
) -> Response:
    """Translate and compile an arXiv paper, returning the resulting PDF as binary."""
    pdf_bytes = await use_case.execute(
        arxiv_paper_id=arxiv_paper_id,
        target_language=target_language,
    )
    filename = f"{arxiv_paper_id.root}_translated.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
