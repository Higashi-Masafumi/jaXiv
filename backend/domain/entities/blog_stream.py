from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, StrictStr

_ChunkType = TypeVar('_ChunkType', bound=Literal['intermediate', 'complete', 'error'])


class _BlogGenerationChunk(BaseModel, Generic[_ChunkType]):
	model_config = ConfigDict(frozen=True)

	type: _ChunkType
	message: StrictStr

	def to_json_string(self) -> str:
		return self.model_dump_json()


class IntermediateBlogChunk(_BlogGenerationChunk[Literal['intermediate']]):
	type: Literal['intermediate'] = 'intermediate'


class CompleteBlogChunk(_BlogGenerationChunk[Literal['complete']]):
	type: Literal['complete'] = 'complete'
	paper_id: StrictStr


class ErrorBlogChunk(_BlogGenerationChunk[Literal['error']]):
	type: Literal['error'] = 'error'
	error_details: StrictStr


TypedBlogChunk = IntermediateBlogChunk | CompleteBlogChunk | ErrorBlogChunk
