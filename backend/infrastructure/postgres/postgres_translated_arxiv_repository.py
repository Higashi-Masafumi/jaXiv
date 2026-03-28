from logging import getLogger

from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.arxiv import (
	ArxivPaperAuthor,
	ArxivPaperMetadataWithTranslatedUrl,
)
from domain.repositories import ITranslatedArxivRepository
from domain.value_objects import ArxivPaperId

from .models import ArxivPaperMetadataWithTranslatedUrlModel


class PostgresTranslatedArxivRepository(ITranslatedArxivRepository):
	"""Repository implementation using PostgreSQL via SQLAlchemy AsyncSession."""

	def __init__(self, session: AsyncSession):
		self._session = session
		self._logger = getLogger(__name__)

	async def find_by_paper_id(
		self, paper_id: ArxivPaperId
	) -> ArxivPaperMetadataWithTranslatedUrl | None:
		statement = select(ArxivPaperMetadataWithTranslatedUrlModel).where(
			col(ArxivPaperMetadataWithTranslatedUrlModel.paper_id) == paper_id.root
		)
		result = await self._session.execute(statement)
		row = result.scalars().first()
		if row is None:
			return None
		return ArxivPaperMetadataWithTranslatedUrl(
			paper_id=ArxivPaperId(row.paper_id),
			title=row.title,
			summary=row.summary,
			published_date=row.published_date,
			authors=[ArxivPaperAuthor(name=author) for author in row.authors],
			source_url=HttpUrl(row.source_url),
			translated_url=HttpUrl(row.translated_url),
			translated_file_storage_path=row.translated_file_storage_path,
		)

	async def save(self, translated_paper_metadata: ArxivPaperMetadataWithTranslatedUrl) -> None:
		statement = select(ArxivPaperMetadataWithTranslatedUrlModel).where(
			col(ArxivPaperMetadataWithTranslatedUrlModel.paper_id)
			== translated_paper_metadata.paper_id.root
		)
		result = await self._session.execute(statement)
		existing = result.scalars().first()
		if existing is not None:
			self._logger.warning('Paper %s already exists', translated_paper_metadata.paper_id.root)
			return
		model = ArxivPaperMetadataWithTranslatedUrlModel(
			paper_id=translated_paper_metadata.paper_id.root,
			title=translated_paper_metadata.title,
			summary=translated_paper_metadata.summary,
			published_date=translated_paper_metadata.published_date,
			authors=[author.name for author in translated_paper_metadata.authors],
			source_url=str(translated_paper_metadata.source_url),
			translated_url=str(translated_paper_metadata.translated_url),
			translated_file_storage_path=translated_paper_metadata.translated_file_storage_path,
		)
		self._session.add(model)
		await self._session.flush()
