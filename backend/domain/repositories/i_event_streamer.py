from abc import ABC, abstractmethod
from pydantic import HttpUrl
from typing import Literal


class IEventStreamer(ABC):
    """
    Interface for event streamer.
    """

    @abstractmethod
    async def stream_event(
        self,
        event_type: Literal["progress", "completed", "failed"],
        message: str,
        arxiv_paper_id: str,
        translated_pdf_url: HttpUrl | None = None,
    ) -> None:
        """
        Stream an event.

        Args:
            event_type (Literal["progress", "completed", "failed"]): The type of the event.
            message (str): The message of the event.
            arxiv_paper_id (str): The arxiv paper id.
            translated_pdf_url (HttpUrl | None, optional): The url of the translated pdf. Defaults to None.

        Returns:
            None

        Raises:
            ValueError: If the event type is invalid.

        Examples:
            >>> event_streamer = EventStreamer()
            >>> await event_streamer.stream_event("progress", "Translating paper 1234567890", "1234567890")
            >>> await event_streamer.stream_event("completed", "Translation completed", "1234567890", HttpUrl("https://example.com/translated.pdf"))
            >>> await event_streamer.stream_event("failed", "Translation failed", "1234567890")
        """
        pass

    @abstractmethod
    async def finish(self) -> None:
        """
        Finish the event streamer.
        """
        pass
