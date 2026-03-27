class DomainError(Exception):
	"""Base class for all domain errors."""

	pass


class ArxivPaperNotFoundError(DomainError):
	"""Raised when an arXiv paper cannot be found."""

	def __init__(self, paper_id: str):
		super().__init__(f'ArXiv paper not found: {paper_id}')
		self.paper_id = paper_id


class TexFileNotFoundError(DomainError):
	"""Raised when no tex file is found in the source directory."""

	def __init__(self, source_directory: str, detail: str = ''):
		message = f'No tex file found in: {source_directory}'
		if detail:
			message += f' ({detail})'
		super().__init__(message)
		self.source_directory = source_directory


class TranslationFailedError(DomainError):
	"""Raised when translation of a LaTeX file fails."""

	def __init__(self, detail: str = ''):
		super().__init__(f'Translation failed: {detail}')
		self.detail = detail


class TranslationEmptyResultError(DomainError):
	"""Raised when translation produces an empty result."""

	def __init__(self):
		super().__init__('Translated text is empty')


class LatexCompilationError(DomainError):
	"""Raised when LaTeX compilation fails."""

	def __init__(self, target_file: str, detail: str = ''):
		super().__init__(f'Error compiling {target_file}: {detail}')
		self.target_file = target_file


class LatexCompilationTimeoutError(DomainError):
	"""Raised when LaTeX compilation times out."""

	def __init__(self, target_file: str):
		super().__init__(f'Timeout compiling {target_file}')
		self.target_file = target_file


class PdfNotGeneratedError(DomainError):
	"""Raised when the compiled PDF file is not found."""

	def __init__(self, pdf_path: str):
		super().__init__(f'PDF file not found after compilation: {pdf_path}')
		self.pdf_path = pdf_path
