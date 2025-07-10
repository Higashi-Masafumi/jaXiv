from fastapi import APIRouter, Depends, Body, Path, Query
from sse_starlette.sse import EventSourceResponse
from usecase import TranslateArxivPaper, SaveTranslatedArxivUsecase, ArxivRedirecter
from domain.entities import ArxivPaperId, TargetLanguage
from infrastructure.arxiv_source_fetcher import ArxivSourceFetcher
from infrastructure.latex_compiler import LatexCompiler
from infrastructure.gemini_latex_translator import GeminiLatexTranslator
from infrastructure.vertex import (
    VertexGeminiLatexTranslator,
)
from infrastructure.postgres import PostgresTranslatedArxivRepository
from infrastructure.supabase import SupabaseStorageRepository
from controller.event_streamer import TranslateArxivEventStreamer
import os
import asyncio

router = APIRouter(prefix="/api/v1/translate")


# ------------------------------------------------------------
# 依存関係の取得
# ------------------------------------------------------------
# イベントストリーマーを取得
def get_event_streamer() -> TranslateArxivEventStreamer:
    return TranslateArxivEventStreamer()


# 翻訳済み論文の取得用usecaseを取得
def get_arxiv_redirecter(
    event_streamer: TranslateArxivEventStreamer = Depends(get_event_streamer),
) -> ArxivRedirecter:
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url is None:
        raise ValueError("POSTGRES_URL is not set")
    return ArxivRedirecter(
        translated_arxiv_repository=PostgresTranslatedArxivRepository(
            postgres_url=postgres_url
        )
    )


# 翻訳用usecaseを取得
def get_translate_arxiv_paper(
    event_streamer: TranslateArxivEventStreamer = Depends(get_event_streamer),
) -> TranslateArxivPaper:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key is None:
        raise ValueError("GEMINI_API_KEY is not set")
    vertex_project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if vertex_project_id is None:
        raise ValueError("VERTEX_PROJECT_ID is not set")
    return TranslateArxivPaper(
        arxiv_source_fetcher=ArxivSourceFetcher(),
        latex_compiler=LatexCompiler(),
        latex_translator=VertexGeminiLatexTranslator(
            project_id=vertex_project_id,
            location="global",
        ),
    )


# 翻訳済み論文の保存用usecaseを取得
def get_save_translated_arxiv(
    event_streamer: TranslateArxivEventStreamer = Depends(get_event_streamer),
) -> SaveTranslatedArxivUsecase:
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url is None:
        raise ValueError("POSTGRES_URL is not set")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    bucket_name = os.getenv("BUCKET_NAME")
    if supabase_url is None:
        raise ValueError("SUPABASE_URL is not set")
    if supabase_key is None:
        raise ValueError("SUPABASE_KEY is not set")
    if bucket_name is None:
        raise ValueError("BUCKET_NAME is not set")

    print("-----------------env----------------")
    print(f"postgres_url: {postgres_url} type: {type(postgres_url)}")
    print(f"supabase_url: {supabase_url} type: {type(supabase_url)}")
    print(f"supabase_key: {supabase_key} type: {type(supabase_key)}")
    print(f"bucket_name: {bucket_name} type: {type(bucket_name)}")
    print("-----------------env----------------")
    return SaveTranslatedArxivUsecase(
        translated_arxiv_repository=PostgresTranslatedArxivRepository(
            postgres_url=postgres_url,
        ),
        file_storage_repository=SupabaseStorageRepository(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            bucket_name=bucket_name,
        ),
        arxiv_source_fetcher=ArxivSourceFetcher(),
    )


# ------------------------------------------------------------
# ルーティング
# ------------------------------------------------------------
@router.get("/arxiv/{arxiv_paper_id}")
async def translate(
    arxiv_paper_id: str = Path(..., description="The ID of the paper"),
    target_language: TargetLanguage = Query(..., description="The target language"),
    event_streamer: TranslateArxivEventStreamer = Depends(get_event_streamer),
    arxiv_redirecter: ArxivRedirecter = Depends(get_arxiv_redirecter),
    translate_arxiv_paper: TranslateArxivPaper = Depends(get_translate_arxiv_paper),
    save_translated_arxiv: SaveTranslatedArxivUsecase = Depends(
        get_save_translated_arxiv
    ),
) -> EventSourceResponse:
    output_dir = os.getenv("OUTPUT_DIR")
    if output_dir is None:
        output_dir = "./output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async def run_workflow():
        # 1. すでに翻訳済みの論文かどうかを確認
        translated_paper_metadata = await arxiv_redirecter.redirect(
            arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
            event_streamer=event_streamer,
        )
        # 2. すでに翻訳済みの論文であれば、翻訳済みのpdfを返却
        if translated_paper_metadata is not None:
            await event_streamer.stream_event(
                event_type="completed",
                message=f"Arxiv {arxiv_paper_id} の翻訳済みpdfのURLは {translated_paper_metadata.translated_url} です。",
                arxiv_paper_id=arxiv_paper_id,
                translated_pdf_url=translated_paper_metadata.translated_url,
            )
            return translated_paper_metadata
        # 3. 翻訳済みの論文でなければ、翻訳を開始
        pdf_file_path = await translate_arxiv_paper.translate(
            arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
            target_language=target_language,
            output_dir=output_dir,
            event_streamer=event_streamer,
        )
        # 4. 翻訳済みの論文として保存
        arxiv_paper_metadata_with_translated_url = (
            await save_translated_arxiv.save_translated_arxiv(
                arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
                translated_arxiv_pdf_path=pdf_file_path,
                event_streamer=event_streamer,
            )
        )
        return arxiv_paper_metadata_with_translated_url

    asyncio.create_task(run_workflow())

    return EventSourceResponse(event_streamer.stream_events(), ping=10)
