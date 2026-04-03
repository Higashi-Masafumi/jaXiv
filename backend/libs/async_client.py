from logging import getLogger

import httpx
from tenacity import (
	before_sleep_log,
	retry,
	retry_if_exception_type,
	stop_after_attempt,
	wait_exponential,
)

_logger = getLogger(__name__)

_retry = retry(
	retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
	stop=stop_after_attempt(3),
	wait=wait_exponential(multiplier=1, min=4, max=15),
	before_sleep=before_sleep_log(_logger, 20),
	reraise=True,
)


class AsyncClient:
	def __init__(self, base_url: str, timeout: float = 30.0) -> None:
		self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout)

	@_retry
	async def get(self, path: str, **kwargs) -> httpx.Response:
		return await self._http.get(path, **kwargs)

	@_retry
	async def post(self, path: str, **kwargs) -> httpx.Response:
		return await self._http.post(path, **kwargs)
