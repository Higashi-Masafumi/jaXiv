from sqlmodel import create_engine, Session, select
from .models import ArxivPaperMetadataWithTranslatedUrlModel
from domain.repositories import ITranslatedArxivRepository
from domain.entities.arxiv import (
    ArxivPaperId,
    ArxivPaperMetadataWithTranslatedUrl,
    ArxivPaperAuthor,
)
from pydantic import HttpUrl
from logging import getLogger


class PostgresTranslatedArxivRepository(ITranslatedArxivRepository):
    def __init__(self, postgres_url: str):
        self._engine = create_engine(postgres_url)
        self._logger = getLogger(__name__)

    def get_translated_paper_metadata(
        self, paper_id: ArxivPaperId
    ) -> ArxivPaperMetadataWithTranslatedUrl | None:
        """
        Fetch the translated metadata of a paper from arXiv.

        Args:
            paper_id (ArxivPaperId): The ID of the paper to fetch the translated metadata for.

        Returns:
            ArxivPaperMetadataWithTranslatedUrl | None: The translated metadata of the paper.
        """
        with Session(self._engine) as session:
            statement = select(ArxivPaperMetadataWithTranslatedUrlModel).where(
                ArxivPaperMetadataWithTranslatedUrlModel.paper_id == paper_id.root
            )
            result = session.exec(statement).first()
            if result is None:
                return None
            return ArxivPaperMetadataWithTranslatedUrl(
                paper_id=ArxivPaperId(root=result.paper_id),
                title=result.title,
                summary=result.summary,
                published_date=result.published_date,
                authors=[ArxivPaperAuthor(name=author) for author in result.authors],
                source_url=HttpUrl(result.source_url),
                translated_url=HttpUrl(result.translated_url),
                translated_file_storage_path=result.translated_file_storage_path,
            )

    def save_translated_paper_metadata(
        self, translated_paper_metadata: ArxivPaperMetadataWithTranslatedUrl
    ) -> None:
        """
        Save the translated metadata of a paper to arXiv.

        Args:
            translated_paper_metadata (ArxivPaperMetadataWithTranslatedUrl): The translated metadata of the paper to save.
        """
        with Session(self._engine) as session:
            translated_paper_metadata_model = ArxivPaperMetadataWithTranslatedUrlModel(
                paper_id=translated_paper_metadata.paper_id.root,
                title=translated_paper_metadata.title,
                summary=translated_paper_metadata.summary,
                published_date=translated_paper_metadata.published_date,
                authors=[author.name for author in translated_paper_metadata.authors],
                source_url=str(translated_paper_metadata.source_url),
                translated_url=str(translated_paper_metadata.translated_url),
                translated_file_storage_path=translated_paper_metadata.translated_file_storage_path,
            )
            session.add(translated_paper_metadata_model)
            session.commit()
