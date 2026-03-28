import re

from pydantic import ConfigDict, RootModel, StrictStr, field_validator
from uuid6 import uuid7

from domain.errors import DomainError


class InvalidPdfPaperIdError(DomainError):
	"""Raised when a PDF-derived paper ID is invalid."""

	def __init__(self, value: str):
		super().__init__(f'Invalid PDF paper ID: {value}')
		self.value = value


class PdfPaperId(RootModel[StrictStr]):
	"""Value Object representing a paper ID for an uploaded PDF.

	Format: ``pdf-<UUID7 hex (32 chars)>``
	UUID7 is time-ordered so IDs sort chronologically.
	"""

	model_config = ConfigDict(frozen=True)

	@field_validator('root')
	@classmethod
	def validate_paper_id(cls, v: str) -> str:
		if not re.match(r'^pdf-[0-9a-f]{32}$', v):
			raise InvalidPdfPaperIdError(v)
		return v

	@classmethod
	def generate(cls) -> 'PdfPaperId':
		"""Generate a new time-ordered PdfPaperId using UUID7."""
		return cls(f'pdf-{uuid7()}')

	def __str__(self) -> str:
		return self.root
