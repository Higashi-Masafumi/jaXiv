from typing import Annotated

from fastapi import APIRouter, Depends
from sse_starlette import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from application.usecase import ChatWithPaperUseCase
from application.chat_events import ChatRequest
from domain.entities.auth_user import AuthUser
from infrastructure.dependencies import (
	get_chat_with_paper_use_case,
	get_required_auth_user,
)

router = APIRouter(prefix='/api/v1/chat')


@router.post(
	'/paper/{paper_id}',
	response_class=EventSourceResponse,
	summary='Chat with a paper using Gemini (SSE stream)',
	responses={
		200: {
			'description': 'SSE stream of ChatStreamEvent objects',
			'content': {'text/event-stream': {}},
		}
	},
)
async def chat_with_paper(
	paper_id: str,
	body: ChatRequest,
	use_case: Annotated[ChatWithPaperUseCase, Depends(get_chat_with_paper_use_case)],
	auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
) -> EventSourceResponse:
	async def generate():
		async for event in use_case.execute(
			paper_id=paper_id,
			message=body.message,
			thread_id=body.thread_id,
			user_id=auth_user.user_id.root,
		):
			yield ServerSentEvent(data=event.model_dump_json())

	return EventSourceResponse(generate(), ping=10)
