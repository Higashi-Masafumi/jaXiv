from pathlib import Path

from domain.entities.figure import ExtractedFigureWithEmbeddings
from domain.gateways.embedding import EmbeddingGateway
from domain.gateways.figure_extractor import FigureExtractorGateway


class ExtractFiguresWithEmbeddingsUseCase:
    """Orchestrates figure extraction and embedding from a PDF file."""

    def __init__(
        self, extractor: FigureExtractorGateway, embedding: EmbeddingGateway
    ) -> None:
        self._extractor = extractor
        self._embedding = embedding

    def execute(self, pdf_path: Path) -> list[ExtractedFigureWithEmbeddings]:
        figures = self._extractor.extract_figures(pdf_path)
        if not figures:
            return []

        image_embeddings = self._embedding.embed_image_batch(
            [fig.image_bytes for fig in figures]
        )
        captions = [fig.caption or "figure" for fig in figures]
        caption_embeddings = self._embedding.embed_text_batch(captions)

        return [
            ExtractedFigureWithEmbeddings(
                **fig.model_dump(),
                image_embeddings=img_emb,
                caption_embeddings=cap_emb,
            )
            for fig, img_emb, cap_emb in zip(figures, image_embeddings, caption_embeddings)
        ]
