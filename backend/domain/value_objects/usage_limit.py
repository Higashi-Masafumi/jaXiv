from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UsageLimit(BaseModel):
	"""Represents a usage limit. ``value`` is None for unlimited tiers."""

	model_config = ConfigDict(frozen=True)

	value: int | None = Field(
		default=None,
		ge=0,
		description='Maximum allowed count. None means unlimited.',
	)

	@classmethod
	def unlimited(cls) -> 'UsageLimit':
		return cls(value=None)

	@classmethod
	def of(cls, value: int) -> 'UsageLimit':
		return cls(value=value)

	def is_unlimited(self) -> bool:
		return self.value is None

	def is_exceeded(self, count: int) -> bool:
		if self.value is None:
			return False
		return count >= self.value
