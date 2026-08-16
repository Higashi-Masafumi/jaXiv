from collections.abc import Iterator
from pathlib import Path

from domain.entities.figure import FigureWithEmbedding
from domain.gateways.i_pdf_figure_analyzer import IPdfFigureAnalyzer
from domain.value_objects.embedding import Embedding
from libs import AsyncClient

from infrastructure.pdf.config import get_pdf_config
from infrastructure.pdf.streaming import pdf_upload_file, post_json_items, write_figure_image

pdf_config = get_pdf_config()


class HttpPdfFigureAnalyzer(IPdfFigureAnalyzer):
	"""Calls the layout-analysis microservice to extract and embed PDF figures."""

	TIMEOUT: float = 300.0
	SERVICE_NAME: str = 'Layout analysis'

	def __init__(self) -> None:
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	def _parse(self, items: Iterator[dict], image_dir: Path) -> list[FigureWithEmbedding]:
		return [
			FigureWithEmbedding(
				image_path=write_figure_image(item, image_dir, index),
				caption=item['caption'],
				figure_number=item['figure_number'],
				page_number=item['page_number'],
				image_embeddings=Embedding(item['image_embeddings']),
				caption_embeddings=Embedding(item['caption_embeddings']),
			)
			for index, item in enumerate(items)
		]

	async def analyze_figures(self, pdf_path: Path, image_dir: Path) -> list[FigureWithEmbedding]:
		with pdf_upload_file(pdf_path) as files:
			async with post_json_items(
				self._client,
				'/analyze/figures',
				service=self.SERVICE_NAME,
				item_prefix='figures.item',
				files=files,
			) as items:
				return self._parse(items, image_dir)

	async def analyze_figures_from_url(
		self, pdf_url: str, image_dir: Path
	) -> list[FigureWithEmbedding]:
		async with post_json_items(
			self._client,
			'/analyze/figures/by-url',
			service=self.SERVICE_NAME,
			item_prefix='figures.item',
			params={'pdf_url': pdf_url},
		) as items:
			return self._parse(items, image_dir)
