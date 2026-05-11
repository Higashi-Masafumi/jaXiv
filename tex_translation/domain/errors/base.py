class DomainError(Exception):
    """Base class for all domain errors."""


class DomainNotFoundError(DomainError):
    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class DomainUnexpectedError(DomainError):
    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail
