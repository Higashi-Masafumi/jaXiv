import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

from domain.entities.embedding import Embedding
from domain.gateways.text_embedding import TextEmbeddingGateway


class NomicTextEmbeddingGateway(TextEmbeddingGateway):
    def __init__(self, model: AutoModel, tokenizer: AutoTokenizer) -> None:
        self._model = model
        self._tokenizer = tokenizer

    def embed_text_batch(self, texts: list[str]) -> list[Embedding]:
        # nomic-embed-text requires task prefix for document embedding
        prefixed = [f"search_document: {t}" for t in texts]
        encoded = self._tokenizer(
            prefixed, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            output = self._model(**encoded)
        token_emb = output.last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1).expand(token_emb.size()).float()
        pooled = torch.sum(token_emb * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)
        return [Embedding(root=e.tolist()) for e in F.normalize(pooled, p=2, dim=1)]
