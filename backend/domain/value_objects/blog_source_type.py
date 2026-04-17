from pydantic import ConfigDict, RootModel, field_validator

from domain.errors import DomainError


class InvalidBlogSourceTypeError(DomainError):
	"""Raised when an invalid blog source type is provided."""

	def __init__(self, value: str):
		super().__init__(f'Invalid blog source type: {value!r}. Expected "arxiv" or "pdf".')
		self.value = value


class BlogSourceType(RootModel[str]):
	"""Value Object representing the source type of a blog post ('arxiv' or 'pdf')."""

	model_config = ConfigDict(frozen=True)

	@field_validator('root')
	@classmethod
	def validate_source_type(cls, v: str) -> str:
		if v not in ('arxiv', 'pdf'):
			raise InvalidBlogSourceTypeError(v)
		return v

	def __str__(self) -> str:
		return self.root

	@property
	def is_arxiv(self) -> bool:
		return self.root == 'arxiv'

	@property
	def is_pdf(self) -> bool:
		return self.root == 'pdf'
