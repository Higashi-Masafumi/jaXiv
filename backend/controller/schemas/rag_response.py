from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from application.usecase.rag_search_image import RagSearchImageResult
from application.usecase.rag_search_text import RagSearchTextResult


class RagSearchRequestSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	query: str = Field(min_length=1)
	limit: int = Field(default=5, ge=1, le=50)


class RagTextChunkSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	text: str
	page_number: int


class RagSearchTextResponseSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	chunks: list[RagTextChunkSchema]

	@classmethod
	def from_result(cls, result: RagSearchTextResult) -> RagSearchTextResponseSchema:
		return cls(
			chunks=[
				RagTextChunkSchema(text=c.text, page_number=c.page_number) for c in result.chunks
			]
		)


class RagImageItemSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_url: str
	caption: str | None
	page_number: int


class RagSearchImageResponseSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	items: list[RagImageItemSchema]

	@classmethod
	def from_result(cls, result: RagSearchImageResult) -> RagSearchImageResponseSchema:
		return cls(
			items=[
				RagImageItemSchema(
					image_url=i.image_url,
					caption=i.caption,
					page_number=i.page_number,
				)
				for i in result.items
			]
		)
