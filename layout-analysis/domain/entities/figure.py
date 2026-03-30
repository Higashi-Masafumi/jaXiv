from pydantic import BaseModel


class ExtractedFigure(BaseModel, frozen=True):
    """A figure extracted from a PDF with its caption and image bytes."""

    image_bytes: bytes
    caption: str
    figure_number: int | None
    page_number: int
