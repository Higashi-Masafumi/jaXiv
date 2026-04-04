from abc import ABC, abstractmethod

from domain.entities.embedding import Embedding


class ImageEmbeddingGateway(ABC):
    @abstractmethod
    def embed_image_batch(self, images: list[bytes]) -> list[Embedding]:
        raise NotImplementedError
