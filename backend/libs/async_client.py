from logging import getLogger
from typing import IO

import httpx
from tenacity import (
	before_sleep_log,
	retry,
	retry_if_exception_type,
	stop_after_attempt,
	wait_exponential,
)

_logger = getLogger(__name__)

# ストリーミング受信時の読み出し単位。この値がそのままメモリ上のピークになる。
DOWNLOAD_CHUNK_SIZE = 1024 * 1024

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

	@_retry
	async def post_to_file(self, path: str, dest: IO[bytes], **kwargs) -> httpx.Response:
		"""POST and stream the response body into ``dest`` instead of buffering it in memory.

		``response.content`` keeps the whole body resident, which is fatal for the
		figure endpoints whose JSON carries every page image as base64. Only error
		bodies (non-200) are read into memory so that ``response.text`` stays usable
		for diagnostics; on success the caller reads ``dest``, which is rewound and
		positioned at 0.
		"""
		dest.seek(0)
		dest.truncate()
		async with self._http.stream('POST', path, **kwargs) as response:
			if response.status_code != 200:
				await response.aread()
				return response
			async for chunk in response.aiter_bytes(chunk_size=DOWNLOAD_CHUNK_SIZE):
				dest.write(chunk)
		dest.flush()
		dest.seek(0)
		return response
