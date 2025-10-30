from typing import AsyncIterator
from fastapi import APIRouter, Depends, Path, Query
from sse_starlette import ServerSentEvent
from sse_starlette.sse import EventSourceResponse
from usecase import TranslateArxivPaper, SaveTranslatedArxivUsecase, ArxivRedirecter
from domain.entities import ArxivPaperId, TargetLanguage, TypedTranslateChunk
from dependency_injector import (
    get_arxiv_redirecter,
    get_translate_arxiv_paper,
    get_save_translated_arxiv,
)
import os
from controller.schemas.translate_response import TranslateResponseSchema

router = APIRouter(prefix="/api/v1/translate")


# ------------------------------------------------------------
# ルーティング
# ------------------------------------------------------------
@router.post("/arxiv/{arxiv_paper_id}")
async def translate_sync(
    arxiv_paper_id: str = Path(..., description="The ID of the paper"),
    target_language: TargetLanguage = Query(..., description="The target language"),
    arxiv_redirecter: ArxivRedirecter = Depends(get_arxiv_redirecter),
    translate_arxiv_paper: TranslateArxivPaper = Depends(get_translate_arxiv_paper),
    save_translated_arxiv: SaveTranslatedArxivUsecase = Depends(
        get_save_translated_arxiv
    ),
) -> TranslateResponseSchema:
    output_dir = os.getenv("OUTPUT_DIR")
    if output_dir is None:
        output_dir = "./output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 1. すでに翻訳済みの論文かどうかを確認
    translated_paper_metadata = await arxiv_redirecter.redirect(
        arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
    )
    if translated_paper_metadata is not None:
        # 翻訳済みの論文であれば、そのURLを返す
        return TranslateResponseSchema(
            message=f"Arxiv {arxiv_paper_id} is already translated.",
            translated_pdf_url=translated_paper_metadata.translated_url,
            translated_language=target_language.value,
        )

    iterator: AsyncIterator[TypedTranslateChunk] = translate_arxiv_paper.translate(
        arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
        target_language=target_language,
        output_dir=output_dir,
    )
    async for chunk in iterator:
        if chunk.type == "complete":
            pdf_file_path = chunk.translated_pdf_path
            break
        elif chunk.type == "error":
            raise Exception(f"Translation failed: {chunk.error_details}")
    else:
        raise Exception("Translation did not complete successfully.")
    # 4. 翻訳済みの論文として保存
    arxiv_paper_metadata_with_translated_url = (
        await save_translated_arxiv.save_translated_arxiv(
            arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
            translated_arxiv_pdf_path=pdf_file_path,
        )
    )
    translated_pdf_url = arxiv_paper_metadata_with_translated_url.translated_url

    return TranslateResponseSchema(
        message=f"Arxiv {arxiv_paper_id} translated successfully.",
        translated_pdf_url=translated_pdf_url,
        translated_language=target_language.value,
    )


@router.get("/arxiv/{arxiv_paper_id}/stream", response_class=EventSourceResponse)
async def translate(
    arxiv_paper_id: str = Path(..., description="The ID of the paper"),
    target_language: TargetLanguage = Query(..., description="The target language"),
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
        )
        if translated_paper_metadata is not None:
            # 翻訳済みの論文であれば、そのURLを返す
            yield ServerSentEvent(data=translated_paper_metadata.translated_url)
            return
        # 3. 翻訳済みの論文でなければ、翻訳を開始
        iterator: AsyncIterator[TypedTranslateChunk] = translate_arxiv_paper.translate(
            arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
            target_language=target_language,
            output_dir=output_dir,
        )
        async for chunk in iterator:
            if chunk.type == "intermediate":
                yield ServerSentEvent(data=chunk.to_json_string())
            elif chunk.type == "complete":
                pdf_file_path = chunk.translated_pdf_path
                yield ServerSentEvent(data=chunk.to_json_string())
                break
            elif chunk.type == "error":
                yield ServerSentEvent(data=chunk.to_json_string())
                return
        else:
            # 正常に完了しなかった場合、エラーチャンクを送信
            raise StopAsyncIteration

        # 4. 翻訳済みの論文として保存
        arxiv_paper_metadata_with_translated_url = (
            await save_translated_arxiv.save_translated_arxiv(
                arxiv_paper_id=ArxivPaperId(root=arxiv_paper_id),
                translated_arxiv_pdf_path=pdf_file_path,
            )
        )
        yield ServerSentEvent(
            data=arxiv_paper_metadata_with_translated_url.translated_url
        )

    return EventSourceResponse(run_workflow(), ping=10)
