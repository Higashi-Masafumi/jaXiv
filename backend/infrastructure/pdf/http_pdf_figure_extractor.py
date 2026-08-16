from pathlib import Path

from domain.entities.figure import ExtractedFigure
from domain.gateways.i_pdf_figure_extractor import IPdfFigureExtractor
from libs import AsyncClient

from infrastructure.pdf.config import get_pdf_config
from infrastructure.pdf.streaming import pdf_upload_file, post_json_items, write_figure_image

pdf_config = get_pdf_config()


class HttpPdfFigureExtractor(IPdfFigureExtractor):
	"""Calls the layout-analysis microservice to extract figures from PDFs."""

	TIMEOUT: float = 120.0
	SERVICE_NAME: str = 'Layout analysis'

	def __init__(self) -> None:
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	async def extract_figures(self, pdf_path: Path, image_dir: Path) -> list[ExtractedFigure]:
		with pdf_upload_file(pdf_path) as files:
			async with post_json_items(
				self._client,
				'/extract-figures',
				service=self.SERVICE_NAME,
				item_prefix='figures.item',
				files=files,
			) as items:
				return [
					ExtractedFigure(
						image_path=write_figure_image(item, image_dir, index),
						caption=item['caption'],
						figure_number=item['figure_number'],
						page_number=item['page_number'],
					)
					for index, item in enumerate(items)
				]
