from abc import ABC, abstractmethod

from domain.entities.embedding import Embedding
from domain.entities.figure import ExtractedFigure


class FigureEmbeddingGateway(ABC):
    """Gateway for embedding figures."""

    @abstractmethod
    def embed_figure(self, figure: ExtractedFigure) -> Embedding:
        """Embed a figure and return its embedding."""
        raise NotImplementedError
