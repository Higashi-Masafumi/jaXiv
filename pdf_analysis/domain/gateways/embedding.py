from abc import ABC, abstractmethod

from domain.entities.embedding import Embedding


class EmbeddingGateway(ABC):
    """Gateway for embedding figures."""

    @abstractmethod
    def embed_text_batch(self, texts: list[str]) -> list[Embedding]:
        """Embed text batch and return its embeddings."""
        raise NotImplementedError

    @abstractmethod
    def embed_image_batch(self, images: list[bytes]) -> list[Embedding]:
        """Embed images and return their embeddings."""
        raise NotImplementedError
