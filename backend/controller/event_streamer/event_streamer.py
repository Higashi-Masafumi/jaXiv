import asyncio
from .models import (
    TranslateArxivEvent,
    TranslateArxivProgressEvent,
    TranslateArxivCompletedEvent,
    TranslateArxivFailedEvent,
    TranslateArxivEventStatus,
)
from domain.repositories import IEventStreamer
from logging import getLogger
from typing import AsyncGenerator, Literal, Dict, Any
from pydantic import HttpUrl
import json

class TranslateArxivEventStreamer(IEventStreamer):
    def __init__(self):
        self._event_queue: asyncio.Queue[TranslateArxivEvent] = asyncio.Queue()
        self._finished: asyncio.Event = asyncio.Event()
        self._logger = getLogger(__name__)

    async def stream_event(
        self,
        event_type: Literal["progress", "completed", "failed"],
        message: str,
        arxiv_paper_id: str,
        progress_percentage: float,
        translated_pdf_url: HttpUrl | None = None,
    ) -> None:
        self._logger.info(f"Streaming event: {event_type} for paper {arxiv_paper_id}")
        match event_type:
            case "progress":
                self._logger.info(
                    f"Streaming progress event for paper {arxiv_paper_id}"
                )
                await self._event_queue.put(
                    TranslateArxivProgressEvent(
                        status=TranslateArxivEventStatus.PROGRESS,
                        arxiv_paper_id=arxiv_paper_id,
                        message=message,
                        progress_percentage=progress_percentage,
                    )
                )
            case "completed" if translated_pdf_url is not None:
                self._logger.info(
                    f"Streaming completed event for paper {arxiv_paper_id}"
                )
                await self._event_queue.put(
                    TranslateArxivCompletedEvent(
                        status=TranslateArxivEventStatus.COMPLETED,
                        arxiv_paper_id=arxiv_paper_id,
                        message=message,
                        translated_pdf_url=translated_pdf_url,
                        progress_percentage=progress_percentage,
                    )
                )
            case "failed":
                self._logger.info(f"Streaming failed event for paper {arxiv_paper_id}")
                await self._event_queue.put(
                    TranslateArxivFailedEvent(
                        status=TranslateArxivEventStatus.FAILED,
                        arxiv_paper_id=arxiv_paper_id,
                        message=message,
                        progress_percentage=progress_percentage,
                    )
                )
            case _:
                raise ValueError(f"Invalid event type: {event_type}")

    async def finish(self) -> None:
        self._finished.set()

    async def stream_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        while not self._finished.is_set():
            event = await self._event_queue.get()
            dumped_event = json.dumps(event.model_dump(mode="json"))
            self._logger.info(f"Yielding event: {dumped_event}")
            yield {"data": dumped_event}

        self._logger.info("Event streamer finished")
