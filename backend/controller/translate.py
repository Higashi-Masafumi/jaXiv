from fastapi import APIRouter, Depends, Form
from usecase.translate_arxiv_paper import TranslateArxivPaper
from domain.entities import ArxivPaperId, TargetLanguage
from infrastructure.arxiv_source_fetcher import ArxivSourceFetcher
from infrastructure.latex_compiler import LatexCompiler
from infrastructure.gemini_latex_translator import GeminiLatexTranslator
import os

router = APIRouter(prefix="/api/v1/translate")


def get_translate_arxiv_paper() -> TranslateArxivPaper:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key is None:
        raise ValueError("GEMINI_API_KEY is not set")
    return TranslateArxivPaper(
        arxiv_source_fetcher=ArxivSourceFetcher(),
        latex_compiler=LatexCompiler(),
        latex_translator=GeminiLatexTranslator(api_key=gemini_api_key),
    )


@router.post("/arxiv")
async def translate(
    arxiv_paper_id: ArxivPaperId = Form(...),
    target_language: TargetLanguage = Form(...),
    translate_arxiv_paper: TranslateArxivPaper = Depends(get_translate_arxiv_paper),
) -> str:
    output_dir = os.getenv("OUTPUT_DIR")
    if output_dir is None:
        output_dir = "./output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    pdf_file_path = await translate_arxiv_paper.translate(
        arxiv_paper_id=arxiv_paper_id,
        target_language=target_language,
        output_dir=output_dir,
    )
    return pdf_file_path
