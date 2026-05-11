from .base import DomainNotFoundError, DomainTimeoutError, DomainUnexpectedError


class ArxivPaperNotFoundError(DomainNotFoundError):
    def __init__(self, paper_id: str) -> None:
        super().__init__(f"ArXiv paper not found: {paper_id}")
        self.paper_id = paper_id


class TexFileNotFoundError(DomainNotFoundError):
    def __init__(self, source_directory: str, detail: str = "") -> None:
        message = f"No tex file found in: {source_directory}"
        if detail:
            message += f" ({detail})"
        super().__init__(message)
        self.source_directory = source_directory


class TranslationFailedError(DomainUnexpectedError):
    def __init__(self, detail: str = "") -> None:
        super().__init__(f"Translation failed: {detail}")


class TranslationEmptyResultError(DomainUnexpectedError):
    def __init__(self) -> None:
        super().__init__("Translated text is empty")


class LatexCompilationError(DomainUnexpectedError):
    def __init__(self, target_file: str, detail: str = "") -> None:
        super().__init__(f"Error compiling {target_file}: {detail}")
        self.target_file = target_file


class LatexCompilationTimeoutError(DomainTimeoutError):
    def __init__(self, target_file: str) -> None:
        super().__init__(f"Timeout compiling {target_file}")
        self.target_file = target_file


class PdfNotGeneratedError(DomainUnexpectedError):
    def __init__(self, pdf_path: str) -> None:
        super().__init__(f"PDF file not found after compilation: {pdf_path}")
        self.pdf_path = pdf_path
