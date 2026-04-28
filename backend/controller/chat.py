import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sse_starlette import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from application.usecase import (
	ChatWithPaperUseCase,
	DeleteChatThreadUseCase,
	GetChatThreadUseCase,
	ListChatThreadsUseCase,
)
from application.chat_events import ChatRequest
from controller.schemas.chat_thread import (
	ChatThreadListResponse,
	ChatThreadResponse,
	ChatThreadSummaryResponse,
)
from domain.entities.auth_user import AuthUser
from infrastructure.dependencies import (
	get_chat_with_paper_use_case,
	get_delete_chat_thread_use_case,
	get_get_chat_thread_use_case,
	get_list_chat_threads_use_case,
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


@router.get(
	'/paper/{paper_id}/threads',
	response_model=ChatThreadListResponse,
	summary='List chat threads for the current user on a paper',
)
async def list_chat_threads(
	paper_id: Annotated[str, Path(description='The paper ID')],
	use_case: Annotated[ListChatThreadsUseCase, Depends(get_list_chat_threads_use_case)],
	_auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
) -> ChatThreadListResponse:
	summaries = await use_case.execute(paper_id=paper_id)
	return ChatThreadListResponse(
		threads=[ChatThreadSummaryResponse.from_summary(s) for s in summaries]
	)


@router.get(
	'/threads/{thread_id}',
	response_model=ChatThreadResponse,
	summary='Get full message history for a chat thread',
)
async def get_chat_thread(
	thread_id: Annotated[uuid.UUID, Path(description='The thread ID')],
	use_case: Annotated[GetChatThreadUseCase, Depends(get_get_chat_thread_use_case)],
	_auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
) -> ChatThreadResponse:
	thread = await use_case.execute(thread_id=thread_id)
	return ChatThreadResponse.from_entity(thread)


@router.delete(
	'/threads/{thread_id}',
	status_code=status.HTTP_204_NO_CONTENT,
	summary='Delete a chat thread owned by the current user',
)
async def delete_chat_thread(
	thread_id: Annotated[uuid.UUID, Path(description='The thread ID')],
	use_case: Annotated[DeleteChatThreadUseCase, Depends(get_delete_chat_thread_use_case)],
	_auth_user: Annotated[AuthUser, Depends(get_required_auth_user)],
) -> None:
	await use_case.execute(thread_id=thread_id)
