from __future__ import annotations

from pydantic import BaseModel, Field

from domain.entities.topic_subscription import TopicSubscription


class UpsertTopicSubscriptionRequest(BaseModel):
	keywords: list[str] = Field(
		default_factory=list,
		description='Keywords to match papers against (normalized server-side)',
	)


class TopicSubscriptionResponse(BaseModel):
	keywords: list[str]
	is_active: bool

	@classmethod
	def from_entity(cls, subscription: TopicSubscription) -> TopicSubscriptionResponse:
		return cls(keywords=subscription.keywords, is_active=subscription.is_active)
