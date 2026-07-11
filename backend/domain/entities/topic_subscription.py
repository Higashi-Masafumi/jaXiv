import uuid
from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.value_objects.user_id import UserId


class TopicSubscription(BaseModel):
	"""A user's topic subscription for the weekly paper-digest email.

	Keyed by ``user_id`` (one subscription per user). ``email`` is captured from
	the user's authenticated token at save time so the background digest job can
	send without a live JWT. ``keywords`` are normalized (see below).
	"""

	MAX_KEYWORDS: ClassVar[int] = 20

	model_config = ConfigDict(frozen=False)

	id: uuid.UUID = Field(default_factory=uuid.uuid4)
	user_id: UserId
	keywords: list[str] = Field(
		default_factory=list, description='Keywords to match papers against'
	)
	is_active: bool = Field(default=True, description='Whether the weekly digest is enabled')
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

	@field_validator('keywords')
	@classmethod
	def _normalize_keywords(cls, raw: list[str]) -> list[str]:
		"""Strip, lowercase, drop blanks, dedupe (order-preserving), cap to MAX_KEYWORDS."""
		normalized: list[str] = []
		seen: set[str] = set()
		for keyword in raw:
			cleaned = keyword.strip().lower()
			if not cleaned or cleaned in seen:
				continue
			seen.add(cleaned)
			normalized.append(cleaned)
		return normalized[: cls.MAX_KEYWORDS]
