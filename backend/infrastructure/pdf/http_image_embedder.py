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
	# 1リクエストにまとめる画像の合計バイト数の上限。base64 文字列と JSON ボディが
	# それぞれ元画像の約1.4倍のサイズで同時に載るため、実測ピークはこの値の5倍前後になる。
	# 枚数で区切ると1枚あたりのサイズ次第でピークが跳ね上がる (8MB x 4枚で +205MB を実測)
	# ため、バイト数で区切って画像の大きさに依存しないようにする。
	MAX_BATCH_BYTES: int = 4 * 1024 * 1024

	def __init__(self) -> None:
		self._logger = getLogger(__name__)
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	async def embed_images(self, items: list[ImageEmbedItem]) -> list[ImageWithEmbedding]:
		batches: list[list[ImageEmbedItem]] = []
		batch_bytes = 0
		for item in items:
			size = item.image_path.stat().st_size
			if batches and batch_bytes + size <= self.MAX_BATCH_BYTES:
				batches[-1].append(item)
				batch_bytes += size
			else:
				# 上限を単独で超える画像も、1枚だけのバッチとして必ず送る。
				batches.append([item])
				batch_bytes = size

		embeddings: list[ImageWithEmbedding] = []
		for index, batch in enumerate(batches, start=1):
			self._logger.info(
				'Embedding image batch %d/%d (%d images)', index, len(batches), len(batch)
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
