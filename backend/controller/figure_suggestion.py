from typing import Annotated

from fastapi import APIRouter, Depends

from application.usecase import SuggestFiguresUseCase
from controller.schemas.figure_suggestion_response import (
	FigureSuggestionRequestSchema,
	FigureSuggestionResponseSchema,
)
from domain.entities.auth_user import AuthUser
from infrastructure.dependencies import (
	get_required_auth_user,
	get_suggest_figures_use_case,
)

router = APIRouter(prefix='/api/v1/figures')


@router.post('/suggest', response_model=FigureSuggestionResponseSchema)
async def suggest_figures(
	body: FigureSuggestionRequestSchema,
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
	use_case: Annotated[SuggestFiguresUseCase, Depends(get_suggest_figures_use_case)],
) -> FigureSuggestionResponseSchema:
	"""Suggest reference figures across all papers from a free-form description."""
	result = await use_case.execute(user_input=body.query, limit=body.limit)
	return FigureSuggestionResponseSchema.from_result(result)
