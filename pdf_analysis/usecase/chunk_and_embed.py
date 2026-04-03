from pathlib import Path

from domain.entities.text_chunk import TextChunkWithEmbeddings
from domain.gateways.pdf_chunker import PdfChunkerGateway
from domain.gateways.text_embedding import TextEmbeddingGateway


class ChunkAndEmbedUseCase:
    """Orchestrates PDF chunking and text embedding."""

    def __init__(self, chunker: PdfChunkerGateway, text_embedding: TextEmbeddingGateway) -> None:
        self._chunker = chunker
        self._text_embedding = text_embedding

    def execute(self, pdf_path: Path) -> list[TextChunkWithEmbeddings]:
        chunks = self._chunker.chunk_pdf(pdf_path)
        if not chunks:
            return []

        embeddings = self._text_embedding.embed_text_batch([chunk.text for chunk in chunks])

        return [
            TextChunkWithEmbeddings(**chunk.model_dump(), text_embeddings=emb)
            for chunk, emb in zip(chunks, embeddings)
        ]
