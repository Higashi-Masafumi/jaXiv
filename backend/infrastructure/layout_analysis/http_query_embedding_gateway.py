import httpx
from typing import Literal

from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_query_embedding_gateway import IQueryEmbeddingGateway
from domain.value_objects.embedding import Embedding
from libs import AsyncClient


class HttpQueryEmbeddingGateway(IQueryEmbeddingGateway):
	"""Calls pdf_analysis ``POST /embed/query`` for BGE or Nomic query vectors."""

	TIMEOUT: float = 60.0

	def __init__(self, service_url: str) -> None:
		self._client = AsyncClient(base_url=service_url, timeout=self.TIMEOUT)

	async def embed_query(self, text: str, kind: Literal['bge', 'nomic']) -> Embedding:
		try:
			response = await self._client.post(
				'/embed/query',
				json={'text': text, 'kind': kind},
			)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'Query embedding service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'Query embedding service returned {response.status_code}: {response.text}'
			)
		data = response.json()
		return Embedding(data['embedding'])
