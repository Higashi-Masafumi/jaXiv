from domain.errors._base import (
	DomainBadRequestError,
	DomainExhaustedError,
	DomainNotFoundError,
	DomainUnexpectedError,
)


class ArxivPaperNotFoundError(DomainNotFoundError):
	"""Raised when an arXiv paper cannot be found."""

	def __init__(self, paper_id: str):
		super().__init__(f'ArXiv paper not found: {paper_id}')
		self.paper_id = paper_id


class TexFileNotFoundError(DomainNotFoundError):
	"""Raised when no tex file is found in the source directory."""

	def __init__(self, source_directory: str, detail: str = ''):
		message = f'No tex file found in: {source_directory}'
		if detail:
			message += f' ({detail})'
		super().__init__(message)
		self.source_directory = source_directory


class TranslationFailedError(DomainUnexpectedError):
	"""Raised when the remote tex_translation service fails to translate."""

	def __init__(self, detail: str = ''):
		super().__init__(f'Translation failed: {detail}')
		self.detail = detail


class LatexCompilationTimeoutError(DomainUnexpectedError):
	"""Raised when LaTeX compilation in the remote tex_translation service times out."""

	def __init__(self, target_file: str):
		super().__init__(f'Timeout compiling {target_file}')
		self.target_file = target_file


class PdfProcessingError(DomainUnexpectedError):
	"""Raised when PDF figure extraction or processing fails."""

	def __init__(self, detail: str = ''):
		super().__init__(f'PDF processing failed: {detail}')
		self.detail = detail


class GenerationLimitExceededError(DomainExhaustedError):
	"""Raised when a user exceeds their monthly blog generation limit."""

	def __init__(self, monthly_count: int, limit: int):
		super().__init__(f'Monthly generation limit exceeded: {monthly_count}/{limit}')
		self.monthly_count = monthly_count
		self.limit = limit


class ChatLimitExceededError(DomainExhaustedError):
	"""Raised when a user exceeds their daily chat message limit."""

	def __init__(self, daily_count: int, limit: int):
		super().__init__(f'Daily chat limit exceeded: {daily_count}/{limit}')
		self.daily_count = daily_count
		self.limit = limit


class ChatThreadNotFoundError(DomainNotFoundError):
	def __init__(self, thread_id: str):
		super().__init__(f'Chat thread not found: {thread_id}')
		self.thread_id = thread_id


class InvalidStripeSignatureError(DomainBadRequestError):
	"""Raised when Stripe webhook signature verification fails."""

	def __init__(self, detail: str = ''):
		super().__init__(f'Invalid Stripe signature: {detail}')
