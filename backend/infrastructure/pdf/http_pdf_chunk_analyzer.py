from pathlib import Path

import httpx

from domain.entities.text_chunk import TextChunkWithEmbedding
from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_pdf_text_chunker import IPdfChunkAnalyzer
from domain.value_objects.embedding import Embedding
from libs import AsyncClient


class HttpPdfChunkAnalyzer(IPdfChunkAnalyzer):
	"""Calls the layout-analysis microservice to chunk and embed PDF text."""

	TIMEOUT: float = 300.0

	def __init__(self, service_url: str) -> None:
		self._client = AsyncClient(base_url=service_url, timeout=self.TIMEOUT)

	def _parse(self, data: dict) -> list[TextChunkWithEmbedding]:
		return [
			TextChunkWithEmbedding(
				text=item['text'],
				page_number=item['page_number'],
				embeddings=Embedding(item['text_embeddings']),
			)
			for item in data['chunks']
		]

	async def analyze_chunks(self, pdf_path: Path) -> list[TextChunkWithEmbedding]:
		try:
			response = await self._client.post(
				'/analyze/chunks',
				files={'file': (pdf_path.name, pdf_path.read_bytes(), 'application/pdf')},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Layout analysis service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Layout analysis service returned {response.status_code}: {response.text}'
			)
		return self._parse(response.json())

	async def analyze_chunks_from_url(self, pdf_url: str) -> list[TextChunkWithEmbedding]:
		try:
			response = await self._client.post(
				'/analyze/chunks/by-url',
				json={'pdf_url': pdf_url},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Layout analysis service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Layout analysis service returned {response.status_code}: {response.text}'
			)
		return self._parse(response.json())
