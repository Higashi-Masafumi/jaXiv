from domain.repositories import ITranslatedArxivRepository, IEventStreamer
from domain.entities import ArxivPaperId, ArxivPaperMetadataWithTranslatedUrl
from logging import getLogger


class ArxivRedirecter:
    def __init__(self, translated_arxiv_repository: ITranslatedArxivRepository):
        self._translated_arxiv_repository = translated_arxiv_repository
        self._logger = getLogger(__name__)

    async def redirect(
        self,
        arxiv_paper_id: ArxivPaperId,
        event_streamer: IEventStreamer,
    ) -> ArxivPaperMetadataWithTranslatedUrl | None:
        translated_paper_metadata = (
            self._translated_arxiv_repository.get_translated_paper_metadata(
                arxiv_paper_id
            )
        )
        if translated_paper_metadata is None:
            self._logger.info(
                "Translated paper metadata not found for %s",
                arxiv_paper_id,
            )
            return None

        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id.root} はすでに翻訳済みのpdfが存在しますので、翻訳済みのpdfを返却します。",
            arxiv_paper_id=arxiv_paper_id.root,
            progress_percentage=100,
        )

        return translated_paper_metadata
