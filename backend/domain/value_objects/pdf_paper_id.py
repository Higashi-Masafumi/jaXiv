import hashlib
import re

from pydantic import ConfigDict, RootModel, StrictStr, field_validator

from domain.errors import DomainError


class InvalidPdfPaperIdError(DomainError):
	"""Raised when a PDF-derived paper ID is invalid."""

	def __init__(self, value: str):
		super().__init__(f'Invalid PDF paper ID: {value}')
		self.value = value


class PdfPaperId(RootModel[StrictStr]):
	"""Value Object representing a paper ID derived from an uploaded PDF.

	Format: 'pdf-<12 hex chars>' where the hex part is the first 12 characters
	of the SHA-256 hash of the paper title.
	"""

	model_config = ConfigDict(frozen=True)

	@field_validator('root')
	@classmethod
	def validate_paper_id(cls, v: str) -> str:
		if not re.match(r'^pdf-[0-9a-f]{12}$', v):
			raise InvalidPdfPaperIdError(v)
		return v

	@classmethod
	def from_title(cls, title: str) -> 'PdfPaperId':
		"""Create a PdfPaperId by hashing the paper title."""
		digest = hashlib.sha256(title.encode()).hexdigest()[:12]
		return cls(f'pdf-{digest}')

	def __str__(self) -> str:
		return self.root
