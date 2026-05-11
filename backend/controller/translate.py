from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from application.usecase import (
	ArxivRedirector,
	SaveTranslatedArxivUseCase,
	TranslateArxivPaper,
)
from controller.schemas.translate_response import TranslateResponseSchema
from domain.value_objects import ArxivPaperId, TargetLanguage
from infrastructure.dependencies import (
	get_arxiv_redirector,
	get_save_translated_arxiv,
	get_translate_arxiv_paper,
)

router = APIRouter(prefix='/api/v1/translate')


@router.post('/arxiv/{arxiv_paper_id}')
async def translate_sync(
	arxiv_paper_id: Annotated[str, Path(description='The ID of the paper')],
	target_language: Annotated[TargetLanguage, Query(description='The target language')],
	arxiv_redirector: Annotated[ArxivRedirector, Depends(get_arxiv_redirector)],
	translate_arxiv_paper: Annotated[TranslateArxivPaper, Depends(get_translate_arxiv_paper)],
	save_translated_arxiv: Annotated[
		SaveTranslatedArxivUseCase, Depends(get_save_translated_arxiv)
	],
) -> TranslateResponseSchema:
	paper_id = ArxivPaperId(arxiv_paper_id)

	already_translated = await arxiv_redirector.execute(arxiv_paper_id=paper_id)
	if already_translated is not None:
		return TranslateResponseSchema(
			message=f'Arxiv {arxiv_paper_id} is already translated.',
			translated_pdf_url=already_translated.translated_url,
			translated_language=target_language.value,
		)

	pdf_bytes = await translate_arxiv_paper.execute(
		arxiv_paper_id=paper_id,
		target_language=target_language,
	)
	metadata = await save_translated_arxiv.execute(
		arxiv_paper_id=paper_id,
		translated_pdf_bytes=pdf_bytes,
	)

	return TranslateResponseSchema(
		message=f'Arxiv {arxiv_paper_id} translated successfully.',
		translated_pdf_url=metadata.translated_url,
		translated_language=target_language.value,
	)
