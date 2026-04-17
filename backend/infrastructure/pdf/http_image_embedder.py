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

	def __init__(self) -> None:
		self._client = AsyncClient(base_url=pdf_config.layout_analysis_url, timeout=self.TIMEOUT)

	async def embed_images(self, items: list[ImageEmbedItem]) -> list[ImageWithEmbedding]:
		if not items:
			return []
		try:
			response = await self._client.post(
				'/embed/images',
				json={
					'items': [
						{'image_base64': item.image_base64, 'caption': item.caption}
						for item in items
					]
				},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Image embedding service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Image embedding service returned {response.status_code}: {response.text}'
			)
		data = response.json()
		return [
			ImageWithEmbedding(
				image_embeddings=Embedding(item['image_embeddings']),
				caption_embeddings=Embedding(item['caption_embeddings']),
			)
			for item in data['items']
		]
