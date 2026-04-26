class DomainError(Exception):
	"""Base class for all domain errors."""

	pass


class DomainBadRequestError(DomainError):
	"""Raised when a bad request is made."""

	def __init__(self, detail: str = ''):
		self.detail = detail


class DomainNotFoundError(DomainError):
	"""Raised when a not found is made."""

	def __init__(self, detail: str = ''):
		self.detail = detail


class DomainUnauthorizedError(DomainError):
	"""Raised when a unauthorized request is made."""

	def __init__(self, detail: str = ''):
		self.detail = detail


class DomainUnexpectedError(DomainError):
	"""Raised when an unexpected error occurs."""

	def __init__(self, detail: str = ''):
		self.detail = detail


class DomainExhaustedError(DomainError):
	"""Raised when a resource is exhausted."""

	def __init__(self, detail: str = ''):
		self.detail = detail
