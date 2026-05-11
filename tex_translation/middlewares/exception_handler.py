from logging import getLogger

from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from domain.errors import (
    DomainBadRequestError,
    DomainNotFoundError,
    DomainTimeoutError,
    DomainUnexpectedError,
)


class ExceptionHandler(BaseHTTPMiddleware):
    """Translate domain errors into HTTP responses uniformly."""

    def __init__(self, app: ASGIApp) -> None:
        self.logger = getLogger(__name__)
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except DomainBadRequestError as e:
            self.logger.warning("DomainBadRequestError: %s", e.detail)
            exc = HTTPException(status_code=400, detail=e.detail)
        except DomainNotFoundError as e:
            self.logger.warning("DomainNotFoundError: %s", e.detail)
            exc = HTTPException(status_code=404, detail=e.detail)
        except DomainTimeoutError as e:
            self.logger.error("DomainTimeoutError: %s", e.detail)
            exc = HTTPException(status_code=504, detail=e.detail)
        except DomainUnexpectedError as e:
            self.logger.error("DomainUnexpectedError: %s", e.detail)
            exc = HTTPException(status_code=500, detail=e.detail)
        except Exception as e:
            self.logger.exception("Unexpected error: %s", e)
            exc = HTTPException(status_code=500, detail="Unexpected error")
        return await http_exception_handler(request, exc)
