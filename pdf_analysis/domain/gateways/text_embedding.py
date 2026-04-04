from abc import ABC, abstractmethod

from domain.entities.embedding import Embedding


class TextEmbeddingGateway(ABC):
    @abstractmethod
    def embed_text_batch(self, texts: list[str]) -> list[Embedding]:
        raise NotImplementedError
