import base64
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

from domain.entities.extracted_figure import ExtractedFigure
from domain.errors.domain_error import PdfProcessingError
from domain.gateways import IPdfFigureExtractor

logger = getLogger(__name__)


class HttpPdfFigureExtractor(IPdfFigureExtractor):
	"""Calls the layout-analysis microservice to extract figures from PDFs."""

	TIMEOUT: float = 120.0

	def __init__(self, service_url: str) -> None:
		self._url = f'{service_url.rstrip("/")}/extract-figures'

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

	def extract_figures(self, pdf_path: Path) -> list[ExtractedFigure]:
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
			ExtractedFigure(
				image_bytes=base64.b64decode(item['image_base64']),
				caption=item['caption'],
				figure_number=item['figure_number'],
				page_number=item['page_number'],
			)
			for item in data['figures']
		]
