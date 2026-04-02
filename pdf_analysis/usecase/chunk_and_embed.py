from pathlib import Path

from domain.entities.text_chunk import TextChunkWithEmbeddings
from domain.gateways.embedding import EmbeddingGateway
from domain.gateways.pdf_chunker import PdfChunkerGateway


class ChunkAndEmbedUseCase:
    """Orchestrates PDF chunking and text embedding."""

    def __init__(self, chunker: PdfChunkerGateway, embedding: EmbeddingGateway) -> None:
        self._chunker = chunker
        self._embedding = embedding

    def execute(self, pdf_path: Path) -> list[TextChunkWithEmbeddings]:
        chunks = self._chunker.chunk_pdf(pdf_path)
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]
        embeddings = self._embedding.embed_text_batch(texts)

        return [
            TextChunkWithEmbeddings(**chunk.model_dump(), text_embeddings=emb)
            for chunk, emb in zip(chunks, embeddings)
        ]
