import httpx
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_query_embedding_gateway import IQueryEmbeddingGateway
from domain.value_objects.embedding import Embedding
from libs import AsyncClient


class LayoutAnalysisConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	layout_analysis_url: str = Field(default='http://localhost:7860')


@lru_cache
def get_layout_analysis_config() -> LayoutAnalysisConfig:
	return LayoutAnalysisConfig()


class HttpQueryEmbeddingGateway(IQueryEmbeddingGateway):
	"""Calls pdf_analysis ``POST /embed/query`` for BGE or Nomic query vectors."""

	TIMEOUT: float = 60.0

	def __init__(self) -> None:
		config = get_layout_analysis_config()
		self._client = AsyncClient(base_url=config.layout_analysis_url, timeout=self.TIMEOUT)

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
