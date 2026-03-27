import os
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sse_starlette import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from controller.schemas.translate_response import TranslateResponseSchema
from domain.entities import TypedTranslateChunk
from domain.errors import TranslationFailedError
from domain.value_objects import ArxivPaperId, TargetLanguage
from infrastructure.dependencies import (
	get_arxiv_redirecter,
	get_save_translated_arxiv,
	get_translate_arxiv_paper,
)
from usecase import ArxivRedirecter, SaveTranslatedArxivUsecase, TranslateArxivPaper

router = APIRouter(prefix='/api/v1/translate')


def _get_output_dir() -> str:
	output_dir = os.getenv('OUTPUT_DIR', './output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	return output_dir


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------
@router.post('/arxiv/{arxiv_paper_id}')
async def translate_sync(
	arxiv_paper_id: Annotated[str, Path(description='The ID of the paper')],
	target_language: Annotated[TargetLanguage, Query(description='The target language')],
	arxiv_redirecter: Annotated[ArxivRedirecter, Depends(get_arxiv_redirecter)],
	translate_arxiv_paper: Annotated[TranslateArxivPaper, Depends(get_translate_arxiv_paper)],
	save_translated_arxiv: Annotated[
		SaveTranslatedArxivUsecase, Depends(get_save_translated_arxiv)
	],
) -> TranslateResponseSchema:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(value=arxiv_paper_id)

	# 1. Check if already translated
	translated_paper_metadata = await arxiv_redirecter.execute(arxiv_paper_id=paper_id)
	if translated_paper_metadata is not None:
		return TranslateResponseSchema(
			message=f'Arxiv {arxiv_paper_id} is already translated.',
			translated_pdf_url=translated_paper_metadata.translated_url,
			translated_language=target_language.value,
		)

	# 2. Translate
	iterator: AsyncIterator[TypedTranslateChunk] = translate_arxiv_paper.execute(
		arxiv_paper_id=paper_id,
		target_language=target_language,
		output_dir=output_dir,
	)
	async for chunk in iterator:
		if chunk.type == 'complete':
			pdf_file_path = chunk.translated_pdf_path
			break
		elif chunk.type == 'error':
			raise TranslationFailedError(chunk.error_details)
	else:
		raise TranslationFailedError('Translation did not complete successfully.')

	# 3. Save
	metadata = await save_translated_arxiv.execute(
		arxiv_paper_id=paper_id,
		translated_arxiv_pdf_path=pdf_file_path,
	)

	return TranslateResponseSchema(
		message=f'Arxiv {arxiv_paper_id} translated successfully.',
		translated_pdf_url=metadata.translated_url,
		translated_language=target_language.value,
	)


@router.get('/arxiv/{arxiv_paper_id}/stream', response_class=EventSourceResponse)
async def translate_stream(
	arxiv_paper_id: Annotated[str, Path(description='The ID of the paper')],
	target_language: Annotated[TargetLanguage, Query(description='The target language')],
	arxiv_redirecter: Annotated[ArxivRedirecter, Depends(get_arxiv_redirecter)],
	translate_arxiv_paper: Annotated[TranslateArxivPaper, Depends(get_translate_arxiv_paper)],
	save_translated_arxiv: Annotated[
		SaveTranslatedArxivUsecase, Depends(get_save_translated_arxiv)
	],
) -> EventSourceResponse:
	output_dir = _get_output_dir()
	paper_id = ArxivPaperId(value=arxiv_paper_id)

	async def run_workflow():
		# 1. Check if already translated
		translated_paper_metadata = await arxiv_redirecter.execute(arxiv_paper_id=paper_id)
		if translated_paper_metadata is not None:
			yield ServerSentEvent(data=translated_paper_metadata.translated_url)
			return

		# 2. Translate with streaming
		iterator = translate_arxiv_paper.execute(
			arxiv_paper_id=paper_id,
			target_language=target_language,
			output_dir=output_dir,
		)
		async for chunk in iterator:
			if chunk.type == 'intermediate':
				yield ServerSentEvent(data=chunk.to_json_string())
			elif chunk.type == 'complete':
				pdf_file_path = chunk.translated_pdf_path
				yield ServerSentEvent(data=chunk.to_json_string())
				break
			elif chunk.type == 'error':
				yield ServerSentEvent(data=chunk.to_json_string())
				return
		else:
			raise StopAsyncIteration

		# 3. Save and return URL
		metadata = await save_translated_arxiv.execute(
			arxiv_paper_id=paper_id,
			translated_arxiv_pdf_path=pdf_file_path,
		)
		yield ServerSentEvent(data=metadata.translated_url)

	return EventSourceResponse(run_workflow(), ping=10)
