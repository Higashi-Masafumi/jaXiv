import base64
from logging import getLogger

import httpx

from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_image_embedder import IImageEmbedder, ImageEmbedItem, ImageWithEmbedding
from domain.value_objects.embedding import Embedding
from libs import AsyncClient

from infrastructure.pdf.config import get_pdf_config

pdf_config = get_pdf_config()


class HttpImageEmbedder(IImageEmbedder):
	"""Calls the pdf_analysis service /embed/images to get image and caption embeddings."""

	TIMEOUT: float = 300.0
	# 1リクエストにまとめる画像数。base64 と JSON ボディが同時にメモリへ載るため、
	# 論文1本分をまとめて送ると数百MBに達しうる。バッチごとに解放して上限を抑える。
	BATCH_SIZE: int = 4

	def __init__(self) -> None:
		self._logger = getLogger(__name__)
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	async def embed_images(self, items: list[ImageEmbedItem]) -> list[ImageWithEmbedding]:
		embeddings: list[ImageWithEmbedding] = []
		for start in range(0, len(items), self.BATCH_SIZE):
			batch = items[start : start + self.BATCH_SIZE]
			self._logger.info(
				'Embedding images %d-%d of %d', start + 1, start + len(batch), len(items)
			)
			try:
				response = await self._client.post(
					'/embed/images',
					json={
						'items': [
							{
								'image_base64': base64.b64encode(
									item.image_path.read_bytes()
								).decode(),
								'caption': item.caption,
							}
							for item in batch
						]
					},
				)
			except (httpx.ConnectError, httpx.TimeoutException) as e:
				raise PdfProcessingError(f'Image embedding service error: {e}') from e
			if response.status_code != 200:
				raise PdfProcessingError(
					f'Image embedding service returned {response.status_code}: {response.text}'
				)
			embeddings.extend(
				ImageWithEmbedding(
					image_embeddings=Embedding(item['image_embeddings']),
					caption_embeddings=Embedding(item['caption_embeddings']),
				)
				for item in response.json()['items']
			)
		return embeddings
