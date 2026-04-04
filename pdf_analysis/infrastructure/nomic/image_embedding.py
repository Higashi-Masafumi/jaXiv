import io

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

from domain.entities.embedding import Embedding
from domain.gateways.image_embedding import ImageEmbeddingGateway


class NomicImageEmbeddingGateway(ImageEmbeddingGateway):
    def __init__(self, model: AutoModel, processor: AutoImageProcessor) -> None:
        self._model = model
        self._processor = processor

    def embed_image_batch(self, images: list[bytes]) -> list[Embedding]:
        pil_images = [Image.open(io.BytesIO(b)).convert("RGB") for b in images]
        inputs = self._processor(pil_images, return_tensors="pt")
        with torch.no_grad():
            outputs = self._model(**inputs)
        embeddings = F.normalize(outputs.last_hidden_state[:, 0], p=2, dim=1)
        return [Embedding(root=e.tolist()) for e in embeddings]
