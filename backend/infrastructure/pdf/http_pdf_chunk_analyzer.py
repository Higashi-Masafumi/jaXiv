from logging import getLogger
from pathlib import Path

import httpx
from tenacity import (
	before_sleep_log,
	retry,
	retry_if_exception_type,
	stop_after_attempt,
	wait_exponential,
)

from domain.entities.text_chunk import TextChunkWithEmbedding
from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_pdf_text_chunker import IPdfChunkAnalyzer
from domain.value_objects.embedding import Embedding

logger = getLogger(__name__)


class HttpPdfChunkAnalyzer(IPdfChunkAnalyzer):
	"""Calls the layout-analysis microservice to chunk and embed PDF text."""

	TIMEOUT: float = 300.0

	def __init__(self, service_url: str) -> None:
		self._url = f'{service_url.rstrip("/")}/analyze/chunks'

	@retry(
		retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
		stop=stop_after_attempt(3),
		wait=wait_exponential(multiplier=2, min=2, max=30),
		before_sleep=before_sleep_log(logger, 20),
		reraise=True,
	)
	def _post(self, pdf_path: Path) -> httpx.Response:
		with open(pdf_path, 'rb') as f:
			return httpx.post(
				self._url,
				files={'file': (pdf_path.name, f, 'application/pdf')},
				timeout=self.TIMEOUT,
			)

	def analyze_chunks(self, pdf_path: Path) -> list[TextChunkWithEmbedding]:
		try:
			response = self._post(pdf_path)
		except httpx.ConnectError as e:
			raise PdfProcessingError(f'Layout analysis service unavailable: {e}') from e
		except httpx.TimeoutException as e:
			raise PdfProcessingError(f'Layout analysis service timed out: {e}') from e

		if response.status_code != 200:
			raise PdfProcessingError(
				f'Layout analysis service returned {response.status_code}: {response.text}'
			)

		data = response.json()
		return [
			TextChunkWithEmbedding(
				text=item['text'],
				page_number=item['page_number'],
				embeddings=Embedding(item['text_embeddings']),
			)
			for item in data['chunks']
		]
