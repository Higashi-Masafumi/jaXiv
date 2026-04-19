from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository
from domain.value_objects.blog_source_type import BlogSourceType
from domain.value_objects.user_id import UserId

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
			source_type=BlogSourceType(row.source_type),
			user_id=UserId(row.user_id) if row.user_id is not None else None,
			created_at=row.created_at,
			updated_at=row.updated_at,
		)

	async def find_all(self, page: int, page_size: int) -> list[BlogPost]:
		"""Return arXiv blog posts only (public)."""
		offset = (page - 1) * page_size
		statement = (
			select(BlogPostContentModel)
			.where(col(BlogPostContentModel.source_type) == 'arxiv')
			.order_by(col(BlogPostContentModel.created_at).desc())
			.offset(offset)
			.limit(page_size)
		)
		result = await self._session.execute(statement)
		rows = result.scalars().all()
		return [self._to_entity(row) for row in rows]

	async def count_all(self) -> int:
		"""Return the total number of arXiv blog posts."""
		statement = (
			select(func.count())
			.select_from(BlogPostContentModel)
			.where(col(BlogPostContentModel.source_type) == 'arxiv')
		)
		result = await self._session.execute(statement)
		return result.scalar_one()

	async def find_all_by_user(self, user_id: UserId, page: int, page_size: int) -> list[BlogPost]:
		"""Return a user's PDF blog posts."""
		offset = (page - 1) * page_size
		statement = (
			select(BlogPostContentModel)
			.where(
				col(BlogPostContentModel.user_id) == user_id.root,
				col(BlogPostContentModel.source_type) == 'pdf',
			)
			.order_by(col(BlogPostContentModel.created_at).desc())
			.offset(offset)
			.limit(page_size)
		)
		result = await self._session.execute(statement)
		rows = result.scalars().all()
		return [self._to_entity(row) for row in rows]

	async def count_all_by_user(self, user_id: UserId) -> int:
		"""Return the total number of PDF blog posts for a given user."""
		statement = (
			select(func.count())
			.select_from(BlogPostContentModel)
			.where(
				col(BlogPostContentModel.user_id) == user_id.root,
				col(BlogPostContentModel.source_type) == 'pdf',
			)
		)
		result = await self._session.execute(statement)
		return result.scalar_one()

	async def count_generated_by_user(self, user_id: UserId, since: datetime | None = None) -> int:
		statement = (
			select(func.count())
			.select_from(BlogPostContentModel)
			.where(col(BlogPostContentModel.user_id) == user_id.root)
		)
		if since is not None:
			statement = statement.where(col(BlogPostContentModel.created_at) >= since)
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
			existing.source_type = blog_post.source_type.root
			existing.user_id = blog_post.user_id.root if blog_post.user_id is not None else None
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
			source_type=blog_post.source_type.root,
			user_id=blog_post.user_id.root if blog_post.user_id is not None else None,
			created_at=now,
			updated_at=now,
		)
		self._session.add(model)
		await self._session.flush()
		return self._to_entity(model)
