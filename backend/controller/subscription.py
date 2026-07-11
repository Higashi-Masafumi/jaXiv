from typing import Annotated

from fastapi import APIRouter, Depends

from application.usecase import (
	GetMyTopicSubscriptionUseCase,
	UpsertTopicSubscriptionUseCase,
)
from controller.schemas.subscription import (
	TopicSubscriptionResponse,
	UpsertTopicSubscriptionRequest,
)
from infrastructure.dependencies import (
	SubscriberIdentity,
	get_get_my_topic_subscription_use_case,
	get_subscriber_identity,
	get_upsert_topic_subscription_use_case,
)

router = APIRouter(prefix='/api/v1/subscriptions')


@router.get('/me', response_model=TopicSubscriptionResponse)
async def get_my_topic_subscription(
	identity: Annotated[SubscriberIdentity, Depends(get_subscriber_identity)],
	use_case: Annotated[
		GetMyTopicSubscriptionUseCase, Depends(get_get_my_topic_subscription_use_case)
	],
) -> TopicSubscriptionResponse:
	subscription = await use_case.execute(user_id=identity.user_id)
	if subscription is None:
		return TopicSubscriptionResponse(keywords=[], is_active=False)
	return TopicSubscriptionResponse.from_entity(subscription)


@router.put('/me', response_model=TopicSubscriptionResponse)
async def upsert_my_topic_subscription(
	body: UpsertTopicSubscriptionRequest,
	identity: Annotated[SubscriberIdentity, Depends(get_subscriber_identity)],
	use_case: Annotated[
		UpsertTopicSubscriptionUseCase, Depends(get_upsert_topic_subscription_use_case)
	],
) -> TopicSubscriptionResponse:
	subscription = await use_case.execute(
		user_id=identity.user_id, email=identity.email, keywords=body.keywords
	)
	return TopicSubscriptionResponse.from_entity(subscription)
