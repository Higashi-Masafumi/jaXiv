from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.figure import ExtractedFigure


class FigureExtractorGateway(ABC):
    """Abstract gateway for extracting figures from a PDF file."""

    @abstractmethod
    def extract_figures(self, pdf_path: Path) -> list[ExtractedFigure]:
        """Extract figures with captions from a PDF file."""
        raise NotImplementedError
