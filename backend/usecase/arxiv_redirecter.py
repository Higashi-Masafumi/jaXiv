from logging import getLogger

from domain.entities import ArxivPaperId, ArxivPaperMetadataWithTranslatedUrl
from domain.repositories import ITranslatedArxivRepository


class ArxivRedirecter:
    def __init__(self, translated_arxiv_repository: ITranslatedArxivRepository):
        self._translated_arxiv_repository = translated_arxiv_repository
        self._logger = getLogger(__name__)

    async def redirect(
        self,
        arxiv_paper_id: ArxivPaperId,
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
        return translated_paper_metadata
