from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from application.usecase.suggest_figures import SuggestFiguresResult


class FigureSuggestionRequestSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	query: str = Field(min_length=1, max_length=2000)
	limit: int = Field(default=24, ge=1, le=60)


class FigureSuggestionItemSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	image_url: str
	caption: str | None
	page_number: int
	paper_id: str
	paper_title: str | None
	score: float
	matched_query: str


class FigureSuggestionResponseSchema(BaseModel):
	model_config = ConfigDict(frozen=True)

	queries: list[str]
	items: list[FigureSuggestionItemSchema]

	@classmethod
	def from_result(cls, result: SuggestFiguresResult) -> FigureSuggestionResponseSchema:
		return cls(
			queries=result.queries,
			items=[
				FigureSuggestionItemSchema(
					image_url=i.image_url,
					caption=i.caption,
					page_number=i.page_number,
					paper_id=i.paper_id,
					paper_title=i.paper_title,
					score=i.score,
					matched_query=i.matched_query,
				)
				for i in result.items
			],
		)
