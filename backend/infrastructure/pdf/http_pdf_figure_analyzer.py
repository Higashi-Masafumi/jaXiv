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

from domain.entities.figure import FigureWithEmbedding
from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_pdf_figure_analyzer import IPdfFigureAnalyzer
from domain.value_objects.embedding import Embedding

logger = getLogger(__name__)


class HttpPdfFigureAnalyzer(IPdfFigureAnalyzer):
	"""Calls the layout-analysis microservice to extract and embed PDF figures."""

	TIMEOUT: float = 300.0

	def __init__(self, service_url: str) -> None:
		base = service_url.rstrip("/")
		self._url_upload = f"{base}/analyze/figures"
		self._url_by_url = f"{base}/analyze/figures/by-url"

	@retry(
		retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
		stop=stop_after_attempt(3),
		wait=wait_exponential(multiplier=2, min=2, max=30),
		before_sleep=before_sleep_log(logger, 20),
		reraise=True,
	)
	def _post_file(self, pdf_path: Path) -> httpx.Response:
		with open(pdf_path, "rb") as f:
			return httpx.post(
				self._url_upload,
				files={"file": (pdf_path.name, f, "application/pdf")},
				timeout=self.TIMEOUT,
			)

	@retry(
		retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
		stop=stop_after_attempt(3),
		wait=wait_exponential(multiplier=2, min=2, max=30),
		before_sleep=before_sleep_log(logger, 20),
		reraise=True,
	)
	def _post_url(self, pdf_url: str) -> httpx.Response:
		return httpx.post(
			self._url_by_url,
			json={"pdf_url": pdf_url},
			timeout=self.TIMEOUT,
		)

	def _parse_figures(self, data: dict) -> list[FigureWithEmbedding]:
		return [
			FigureWithEmbedding(
				image_bytes=base64.b64decode(item["image_base64"]),
				caption=item["caption"],
				figure_number=item["figure_number"],
				page_number=item["page_number"],
				image_embeddings=Embedding(item["image_embeddings"]),
				caption_embeddings=Embedding(item["caption_embeddings"]),
			)
			for item in data["figures"]
		]

	def _handle_response(self, response: httpx.Response) -> list[FigureWithEmbedding]:
		if response.status_code != 200:
			raise PdfProcessingError(
				f"Layout analysis service returned {response.status_code}: {response.text}"
			)
		return self._parse_figures(response.json())

	def analyze_figures(self, pdf_path: Path) -> list[FigureWithEmbedding]:
		try:
			response = self._post_file(pdf_path)
		except httpx.ConnectError as e:
			raise PdfProcessingError(f"Layout analysis service unavailable: {e}") from e
		except httpx.TimeoutException as e:
			raise PdfProcessingError(f"Layout analysis service timed out: {e}") from e
		return self._handle_response(response)

	def analyze_figures_from_url(self, pdf_url: str) -> list[FigureWithEmbedding]:
		try:
			response = self._post_url(pdf_url)
		except httpx.ConnectError as e:
			raise PdfProcessingError(f"Layout analysis service unavailable: {e}") from e
		except httpx.TimeoutException as e:
			raise PdfProcessingError(f"Layout analysis service timed out: {e}") from e
		return self._handle_response(response)
