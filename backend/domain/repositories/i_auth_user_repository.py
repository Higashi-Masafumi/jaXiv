from abc import ABC, abstractmethod

from domain.value_objects.user_id import UserId


class IAuthUserRepository(ABC):
	"""Reads authenticated-user attributes managed by Supabase Auth."""

	@abstractmethod
	async def find_email(self, user_id: UserId) -> str | None:
		"""Return the user's email, or None if they have none / do not exist."""
		raise NotImplementedError
