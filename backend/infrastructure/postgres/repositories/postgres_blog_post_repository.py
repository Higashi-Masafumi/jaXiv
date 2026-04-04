from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository

from ..models import BlogPostContentModel


class PostgresBlogPostRepository(IBlogPostRepository):
	"""Repository implementation for blog posts using PostgreSQL via SQLAlchemy AsyncSession."""

	def __init__(self, session: AsyncSession):
		self._session = session
		self._logger = getLogger(__name__)

	def _to_entity(self, row: BlogPostContentModel) -> BlogPost:
		return BlogPost(
			id=row.id,
			paper_id=row.paper_id,
			title=row.title or '',
			summary=row.summary or '',
			authors=row.authors or [],
			source_url=row.source_url,
			content=row.content,
			created_at=row.created_at,
			updated_at=row.updated_at,
		)

	async def find_all(self, page: int, page_size: int) -> list[BlogPost]:
		offset = (page - 1) * page_size
		statement = (
			select(BlogPostContentModel)
			.order_by(col(BlogPostContentModel.created_at).desc())
			.offset(offset)
			.limit(page_size)
		)
		result = await self._session.execute(statement)
		rows = result.scalars().all()
		return [self._to_entity(row) for row in rows]

	async def count_all(self) -> int:
		statement = select(func.count()).select_from(BlogPostContentModel)
		result = await self._session.execute(statement)
		return result.scalar_one()

	async def find_by_paper_id(self, paper_id: str) -> BlogPost | None:
		statement = select(BlogPostContentModel).where(
			col(BlogPostContentModel.paper_id) == paper_id
		)
		result = await self._session.execute(statement)
		row = result.scalars().first()
		if row is None:
			return None
		return self._to_entity(row)

	async def save(self, blog_post: BlogPost) -> BlogPost:
		statement = select(BlogPostContentModel).where(
			col(BlogPostContentModel.paper_id) == blog_post.paper_id
		)
		result = await self._session.execute(statement)
		existing = result.scalars().first()
		now = datetime.now(UTC)
		if existing is not None:
			existing.title = blog_post.title
			existing.summary = blog_post.summary
			existing.authors = blog_post.authors
			existing.source_url = blog_post.source_url
			existing.content = blog_post.content
			existing.updated_at = now
			await self._session.flush()
			return self._to_entity(existing)
		model = BlogPostContentModel(
			paper_id=blog_post.paper_id,
			title=blog_post.title,
			summary=blog_post.summary,
			authors=blog_post.authors,
			source_url=blog_post.source_url,
			content=blog_post.content,
			created_at=now,
			updated_at=now,
		)
		self._session.add(model)
		await self._session.flush()
		return self._to_entity(model)
