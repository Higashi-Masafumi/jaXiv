import uuid

from pydantic import ConfigDict, RootModel


class UserId(RootModel[uuid.UUID]):
	"""Value Object representing a Supabase user UUID."""

	model_config = ConfigDict(frozen=True)

	def __str__(self) -> str:
		return str(self.root)
