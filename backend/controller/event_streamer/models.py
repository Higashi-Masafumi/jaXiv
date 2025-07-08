from pydantic import BaseModel, StrictStr, Field, HttpUrl
import enum
from typing import Union


class TranslateArxivEventStatus(str, enum.Enum):
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslateArxivProgressEvent(BaseModel):
    status: TranslateArxivEventStatus = TranslateArxivEventStatus.PROGRESS
    arxiv_paper_id: StrictStr
    message: StrictStr = Field(description="The message of the event")


class TranslateArxivCompletedEvent(BaseModel):
    status: TranslateArxivEventStatus = TranslateArxivEventStatus.COMPLETED
    arxiv_paper_id: StrictStr
    message: StrictStr = Field(description="The message of the event")
    translated_pdf_url: HttpUrl


class TranslateArxivFailedEvent(BaseModel):
    status: TranslateArxivEventStatus = TranslateArxivEventStatus.FAILED
    arxiv_paper_id: StrictStr
    message: StrictStr = Field(
        default="翻訳したtexファイルのコンパイルに失敗しました。入力されたarxiv idのtexファイルが非対応の可能性があります。",
        description="The message of the event",
    )


TranslateArxivEvent = Union[
    TranslateArxivProgressEvent,
    TranslateArxivCompletedEvent,
    TranslateArxivFailedEvent,
]
