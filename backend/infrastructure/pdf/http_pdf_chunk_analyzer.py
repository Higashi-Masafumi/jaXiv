from collections.abc import Iterator
from pathlib import Path

from domain.entities.text_chunk import TextChunkWithEmbedding
from domain.gateways.i_pdf_text_chunker import IPdfChunkAnalyzer
from domain.value_objects.embedding import Embedding
from libs import AsyncClient

from infrastructure.pdf.config import get_pdf_config
from infrastructure.pdf.streaming import pdf_upload_file, post_json_items

pdf_config = get_pdf_config()


class HttpPdfChunkAnalyzer(IPdfChunkAnalyzer):
	"""Calls the layout-analysis microservice to chunk and embed PDF text."""

	TIMEOUT: float = 300.0
	SERVICE_NAME: str = 'Layout analysis'

	def __init__(self) -> None:
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	def _parse(self, items: Iterator[dict]) -> list[TextChunkWithEmbedding]:
		return [
			TextChunkWithEmbedding(
				text=item['text'],
				page_number=item['page_number'],
				embeddings=Embedding(item['text_embeddings']),
			)
			for item in items
		]

	async def analyze_chunks(self, pdf_path: Path) -> list[TextChunkWithEmbedding]:
		with pdf_upload_file(pdf_path) as files:
			async with post_json_items(
				self._client,
				'/analyze/chunks',
				service=self.SERVICE_NAME,
				item_prefix='chunks.item',
				files=files,
			) as items:
				return self._parse(items)

	async def analyze_chunks_from_url(self, pdf_url: str) -> list[TextChunkWithEmbedding]:
		async with post_json_items(
			self._client,
			'/analyze/chunks/by-url',
			service=self.SERVICE_NAME,
			item_prefix='chunks.item',
			params={'pdf_url': pdf_url},
		) as items:
			return self._parse(items)
