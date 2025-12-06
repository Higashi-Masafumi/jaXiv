from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, StrictInt, StrictStr

_ChunkType = TypeVar('_ChunkType', bound=Literal['intermediate', 'complete', 'error'])


class _TranslateChunk(BaseModel, Generic[_ChunkType]):
	type: _ChunkType
	message: StrictStr
	progress_percentage: StrictInt

	def to_json_string(self) -> str:
		return self.model_dump_json()


class IntermediateTranslateChunk(_TranslateChunk[Literal['intermediate']]):
	type: Literal['intermediate'] = 'intermediate'


class CompleteTranslateChunk(_TranslateChunk[Literal['complete']]):
	type: Literal['complete'] = 'complete'
	translated_pdf_path: StrictStr


class ErrorTranslateChunk(_TranslateChunk[Literal['error']]):
	type: Literal['error'] = 'error'
	error_details: StrictStr


TypedTranslateChunk = IntermediateTranslateChunk | CompleteTranslateChunk | ErrorTranslateChunk
