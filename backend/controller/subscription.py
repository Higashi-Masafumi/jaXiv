import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from application.usecase import (
	GetMyTopicSubscriptionUseCase,
	SendWeeklyDigestsUseCase,
	UpsertTopicSubscriptionUseCase,
)
from controller.schemas.subscription import (
	DigestRunResultResponse,
	TopicSubscriptionResponse,
	UpsertTopicSubscriptionRequest,
)
from domain.value_objects.user_id import UserId
from infrastructure.dependencies import (
	get_get_my_topic_subscription_use_case,
	get_required_user_id,
	get_send_weekly_digests_use_case,
	get_upsert_topic_subscription_use_case,
	verify_job_admin_token,
)

router = APIRouter(prefix='/api/v1/subscriptions')


@router.get('/me', response_model=TopicSubscriptionResponse)
async def get_my_topic_subscription(
	user_id: Annotated[uuid.UUID, Depends(get_required_user_id)],
	use_case: Annotated[
		GetMyTopicSubscriptionUseCase, Depends(get_get_my_topic_subscription_use_case)
	],
) -> TopicSubscriptionResponse:
	subscription = await use_case.execute(user_id=UserId(user_id))
	if subscription is None:
		return TopicSubscriptionResponse(keywords=[], is_active=False)
	return TopicSubscriptionResponse.from_entity(subscription)


@router.put('/me', response_model=TopicSubscriptionResponse)
async def upsert_my_topic_subscription(
	body: UpsertTopicSubscriptionRequest,
	user_id: Annotated[uuid.UUID, Depends(get_required_user_id)],
	use_case: Annotated[
		UpsertTopicSubscriptionUseCase, Depends(get_upsert_topic_subscription_use_case)
	],
) -> TopicSubscriptionResponse:
	subscription = await use_case.execute(user_id=UserId(user_id), keywords=body.keywords)
	return TopicSubscriptionResponse.from_entity(subscription)


@router.post(
	'/internal/send-weekly-digests',
	response_model=DigestRunResultResponse,
	dependencies=[Depends(verify_job_admin_token)],
)
async def send_weekly_digests(
	use_case: Annotated[SendWeeklyDigestsUseCase, Depends(get_send_weekly_digests_use_case)],
) -> DigestRunResultResponse:
	"""Trigger the weekly digest send for all active subscribers (job-token protected)."""
	result = await use_case.execute()
	return DigestRunResultResponse.from_result(result)
