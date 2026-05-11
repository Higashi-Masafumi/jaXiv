class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class DomainBadRequestError(DomainError):
    """The caller supplied invalid input (4xx / 400)."""


class DomainNotFoundError(DomainError):
    """The requested resource does not exist (4xx / 404)."""


class DomainTimeoutError(DomainError):
    """An upstream dependency timed out (5xx / 504)."""


class DomainUnexpectedError(DomainError):
    """Catch-all for unexpected failures (5xx / 500)."""
