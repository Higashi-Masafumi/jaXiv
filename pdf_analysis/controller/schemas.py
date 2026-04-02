from pydantic import BaseModel, ConfigDict


class FigureResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_base64: str
    caption: str
    figure_number: int | None
    page_number: int


class ExtractFiguresResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    figures: list[FigureResponse]
