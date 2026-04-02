from pathlib import Path

from domain.entities.figure import ExtractedFigure
from infrastructure.onnx.pdf_figure_extractor import PdfFigureExtractor


class ExtractFiguresUseCase:
    """Orchestrates figure extraction from a PDF file."""

    def __init__(self, extractor: PdfFigureExtractor) -> None:
        self._extractor = extractor

    def execute(self, pdf_path: Path) -> list[ExtractedFigure]:
        return self._extractor.extract_figures(pdf_path)
