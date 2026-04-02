from abc import ABC, abstractmethod
from pathlib import Path
from domain.entities.chunk import TextChunk


class PdfChunkerGateway(ABC):
    """Gateway for chunking a PDF file into text chunks."""

    @abstractmethod
    def chunk_pdf(self, pdf_path: Path) -> list[TextChunk]:
        """Chunk a PDF file into text chunks."""
        raise NotImplementedError
