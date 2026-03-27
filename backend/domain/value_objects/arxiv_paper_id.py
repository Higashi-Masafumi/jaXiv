import re

from pydantic import BaseModel, ConfigDict, field_validator

from domain.errors import DomainError


class InvalidArxivPaperIdError(DomainError):
	"""Raised when an arXiv paper ID is invalid."""

	def __init__(self, value: str):
		super().__init__(f'Invalid arXiv paper ID: {value}')
		self.value = value


class ArxivPaperId(BaseModel):
	"""Value Object representing an arXiv paper ID (e.g. '2301.12345' or '2301.12345v2')."""

	model_config = ConfigDict(frozen=True)

	value: str

	@field_validator('value')
	@classmethod
	def validate_paper_id(cls, v: str) -> str:
		# arXiv paper IDs follow the pattern YYMM.NNNNN or YYMM.NNNNNvN
		if not re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', v):
			raise InvalidArxivPaperIdError(v)
		return v
