from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageLimit:
	"""Represents a usage limit. ``value`` is None for unlimited tiers."""

	value: int | None

	@classmethod
	def unlimited(cls) -> 'UsageLimit':
		return cls(value=None)

	@classmethod
	def of(cls, value: int) -> 'UsageLimit':
		if value < 0:
			raise ValueError('UsageLimit value must be non-negative')
		return cls(value=value)

	def is_unlimited(self) -> bool:
		return self.value is None

	def is_exceeded(self, count: int) -> bool:
		if self.value is None:
			return False
		return count >= self.value
