from pydantic import BaseModel, ConfigDict
from domain.entities.embedding import Embedding


class TextChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    page_number: int
    text_embeddings: Embedding
