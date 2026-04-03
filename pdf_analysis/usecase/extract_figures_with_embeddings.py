from pathlib import Path

from domain.entities.figure import ExtractedFigureWithEmbeddings
from domain.gateways.figure_extractor import FigureExtractorGateway
from domain.gateways.image_embedding import ImageEmbeddingGateway
from domain.gateways.text_embedding import TextEmbeddingGateway


class ExtractFiguresWithEmbeddingsUseCase:
    """Orchestrates figure extraction and embedding from a PDF file."""

    def __init__(
        self,
        extractor: FigureExtractorGateway,
        image_embedding: ImageEmbeddingGateway,
        caption_embedding: TextEmbeddingGateway,
    ) -> None:
        self._extractor = extractor
        self._image_embedding = image_embedding
        self._caption_embedding = caption_embedding

    def execute(self, pdf_path: Path) -> list[ExtractedFigureWithEmbeddings]:
        figures = self._extractor.extract_figures(pdf_path)
        if not figures:
            return []

        image_embeddings = self._image_embedding.embed_image_batch(
            [fig.image_bytes for fig in figures]
        )
        captions = [fig.caption or "figure" for fig in figures]
        caption_embeddings = self._caption_embedding.embed_text_batch(captions)

        return [
            ExtractedFigureWithEmbeddings(
                **fig.model_dump(),
                image_embeddings=img_emb,
                caption_embeddings=cap_emb,
            )
            for fig, img_emb, cap_emb in zip(
                figures, image_embeddings, caption_embeddings
            )
        ]
