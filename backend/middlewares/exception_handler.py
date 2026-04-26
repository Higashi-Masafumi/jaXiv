from logging import getLogger

from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from domain.errors import (
	DomainBadRequestError,
	DomainExhaustedError,
	DomainNotFoundError,
	DomainUnauthorizedError,
	DomainUnexpectedError,
)


class ExceptionHandler(BaseHTTPMiddleware):
	def __init__(self, app: ASGIApp) -> None:
		self.logger = getLogger(__name__)
		super().__init__(app)

	async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
		try:
			return await call_next(request)
		except DomainBadRequestError as e:
			self.logger.error(f'DomainBadRequestError: {e.detail}')
			exc = HTTPException(status_code=400, detail=e.detail)
		except DomainNotFoundError as e:
			self.logger.error(f'DomainNotFoundError: {e.detail}')
			exc = HTTPException(status_code=404, detail=e.detail)
		except DomainExhaustedError as e:
			self.logger.error(f'DomainExhaustedError: {e.detail}')
			exc = HTTPException(status_code=403, detail=e.detail)
		except DomainUnauthorizedError as e:
			self.logger.error(f'DomainUnauthorizedError: {e.detail}')
			exc = HTTPException(status_code=401, detail=e.detail)
		except DomainUnexpectedError as e:
			self.logger.error(f'DomainUnexpectedError: {e.detail}')
			exc = HTTPException(status_code=500, detail=e.detail)
		except Exception as e:
			self.logger.error(f'Unexpected error: {e}')
			exc = HTTPException(status_code=500, detail='Unexpected error')
		return await http_exception_handler(request, exc)
