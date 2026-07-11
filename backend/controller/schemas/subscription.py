from __future__ import annotations

from pydantic import BaseModel, Field

from application.usecase import DigestRunResult
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


class DigestRunResultResponse(BaseModel):
	sent: int
	skipped: int
	failed: int

	@classmethod
	def from_result(cls, result: DigestRunResult) -> DigestRunResultResponse:
		return cls(sent=result.sent, skipped=result.skipped, failed=result.failed)
