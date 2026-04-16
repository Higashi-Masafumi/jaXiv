import base64
from pathlib import Path

import httpx

from domain.entities.figure import FigureWithEmbedding
from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_pdf_figure_analyzer import IPdfFigureAnalyzer
from domain.value_objects.embedding import Embedding
from libs import AsyncClient

from infrastructure.pdf.config import get_pdf_config

pdf_config = get_pdf_config()


class HttpPdfFigureAnalyzer(IPdfFigureAnalyzer):
	"""Calls the layout-analysis microservice to extract and embed PDF figures."""

	TIMEOUT: float = 300.0

	def __init__(self) -> None:
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	def _parse(self, data: dict) -> list[FigureWithEmbedding]:
		return [
			FigureWithEmbedding(
				image_bytes=base64.b64decode(item['image_base64']),
				caption=item['caption'],
				figure_number=item['figure_number'],
				page_number=item['page_number'],
				image_embeddings=Embedding(item['image_embeddings']),
				caption_embeddings=Embedding(item['caption_embeddings']),
			)
			for item in data['figures']
		]

	async def analyze_figures(self, pdf_path: Path) -> list[FigureWithEmbedding]:
		try:
			response = await self._client.post(
				'/analyze/figures',
				files={'file': (pdf_path.name, pdf_path.read_bytes(), 'application/pdf')},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Layout analysis service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Layout analysis service returned {response.status_code}: {response.text}'
			)
		return self._parse(response.json())

	async def analyze_figures_from_url(self, pdf_url: str) -> list[FigureWithEmbedding]:
		try:
			response = await self._client.post(
				'/analyze/figures/by-url',
				params={'pdf_url': pdf_url},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Layout analysis service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Layout analysis service returned {response.status_code}: {response.text}'
			)
		return self._parse(response.json())
