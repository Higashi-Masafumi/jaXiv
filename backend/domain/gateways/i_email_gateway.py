from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class DigestItem(BaseModel):
	"""A single paper card shown in a weekly digest email."""

	model_config = ConfigDict(frozen=True)

	paper_id: str
	title: str
	summary: str


class IEmailGateway(ABC):
	"""Gateway for sending transactional emails."""

	@abstractmethod
	async def send_weekly_digest(self, to: str, items: list[DigestItem]) -> None:
		"""Send a weekly digest email listing ``items`` to ``to``.

		Raises ``EmailDeliveryError`` if the provider rejects the send.
		"""
		raise NotImplementedError
