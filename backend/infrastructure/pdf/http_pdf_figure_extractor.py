import base64
from pathlib import Path

import httpx

from domain.entities.figure import ExtractedFigure
from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_pdf_figure_extractor import IPdfFigureExtractor
from libs import AsyncClient


class HttpPdfFigureExtractor(IPdfFigureExtractor):
	"""Calls the layout-analysis microservice to extract figures from PDFs."""

	TIMEOUT: float = 120.0

	def __init__(self, service_url: str) -> None:
		self._client = AsyncClient(base_url=service_url, timeout=self.TIMEOUT)

	def _parse(self, data: dict) -> list[ExtractedFigure]:
		return [
			ExtractedFigure(
				image_bytes=base64.b64decode(item['image_base64']),
				caption=item['caption'],
				figure_number=item['figure_number'],
				page_number=item['page_number'],
			)
			for item in data['figures']
		]

	async def extract_figures(self, pdf_path: Path) -> list[ExtractedFigure]:
		try:
			response = await self._client.post(
				'/extract-figures',
				files={'file': (pdf_path.name, pdf_path.read_bytes(), 'application/pdf')},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Layout analysis service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Layout analysis service returned {response.status_code}: {response.text}'
			)
		return self._parse(response.json())
