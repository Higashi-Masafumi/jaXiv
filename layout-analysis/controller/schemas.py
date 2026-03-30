from pydantic import BaseModel


class FigureResponse(BaseModel, frozen=True):
    image_base64: str
    caption: str
    figure_number: int | None
    page_number: int


class ExtractFiguresResponse(BaseModel, frozen=True):
    figures: list[FigureResponse]
