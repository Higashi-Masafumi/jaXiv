from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from domain.entities.embedding import Embedding
from domain.gateways.embedding import EmbeddingGateway


class HuggingFaceEmbeddingGateway(EmbeddingGateway):
    """Gateway for embedding text and images using Hugging Face."""

    def __init__(self, model: HuggingFaceEmbedding) -> None:
        self._model = model

    def embed_text_batch(self, texts: list[str]) -> list[Embedding]:
        embeddings = self._model.get_text_embedding_batch(texts)
        return [Embedding(root=e) for e in embeddings]

    def embed_image_batch(self, images: list[bytes]) -> list[Embedding]:
        embeddings = self._model.get_image_embedding_batch(images)
        return [Embedding(root=e) for e in embeddings]
