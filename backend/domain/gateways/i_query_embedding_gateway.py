from abc import ABC, abstractmethod
from typing import Literal

from domain.value_objects.embedding import Embedding


class IQueryEmbeddingGateway(ABC):
	"""Embeds a user query via layout-analysis (BGE / Nomic) for Qdrant RAG."""

	@abstractmethod
	async def embed_query(self, text: str, kind: Literal['bge', 'nomic']) -> Embedding:
		raise NotImplementedError
