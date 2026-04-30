from domain.errors._base import DomainExhaustedError, DomainNotFoundError, DomainUnexpectedError


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
	"""Raised when translation of a LaTeX file fails."""

	def __init__(self, detail: str = ''):
		super().__init__(f'Translation failed: {detail}')
		self.detail = detail


class TranslationEmptyResultError(DomainUnexpectedError):
	"""Raised when translation produces an empty result."""

	def __init__(self):
		super().__init__('Translated text is empty')


class LatexCompilationError(DomainUnexpectedError):
	"""Raised when LaTeX compilation fails."""

	def __init__(self, target_file: str, detail: str = ''):
		super().__init__(f'Error compiling {target_file}: {detail}')
		self.target_file = target_file


class LatexCompilationTimeoutError(DomainUnexpectedError):
	"""Raised when LaTeX compilation times out."""

	def __init__(self, target_file: str):
		super().__init__(f'Timeout compiling {target_file}')
		self.target_file = target_file


class PdfNotGeneratedError(DomainUnexpectedError):
	"""Raised when the compiled PDF file is not found."""

	def __init__(self, pdf_path: str):
		super().__init__(f'PDF file not found after compilation: {pdf_path}')
		self.pdf_path = pdf_path


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
