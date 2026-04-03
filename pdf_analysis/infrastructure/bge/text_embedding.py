import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

from domain.entities.embedding import Embedding
from domain.gateways.text_embedding import TextEmbeddingGateway


class BgeTextEmbeddingGateway(TextEmbeddingGateway):
    def __init__(self, model: AutoModel, tokenizer: AutoTokenizer) -> None:
        self._model = model
        self._tokenizer = tokenizer

    def embed_text_batch(self, texts: list[str]) -> list[Embedding]:
        encoded = self._tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            output = self._model(**encoded)
        # BGE uses CLS token pooling
        embeddings = F.normalize(output.last_hidden_state[:, 0], p=2, dim=1)
        return [Embedding(root=e.tolist()) for e in embeddings]
