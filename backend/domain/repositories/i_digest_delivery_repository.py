import uuid
from abc import ABC, abstractmethod

from domain.value_objects.user_id import UserId


class IDigestDeliveryRepository(ABC):
	"""Tracks which blog posts have already been emailed to each user."""

	@abstractmethod
	async def find_delivered_blog_ids(self, user_id: UserId) -> set[uuid.UUID]:
		"""Return the ids of blog posts already delivered to the user."""
		raise NotImplementedError

	@abstractmethod
	async def record_deliveries(self, user_id: UserId, blog_ids: list[uuid.UUID]) -> None:
		"""Record that the given blog posts were delivered to the user (idempotent)."""
		raise NotImplementedError
