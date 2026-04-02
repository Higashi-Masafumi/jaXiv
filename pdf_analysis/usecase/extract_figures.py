from pathlib import Path

from domain.entities.figure import ExtractedFigure
from domain.gateways.figure_extractor import FigureExtractorGateway


class ExtractFiguresUseCase:
    """Orchestrates figure extraction from a PDF file."""

    def __init__(self, extractor: FigureExtractorGateway) -> None:
        self._extractor = extractor

    def execute(self, pdf_path: Path) -> list[ExtractedFigure]:
        return self._extractor.extract_figures(pdf_path)
