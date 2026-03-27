from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from domain.entities.blog import BlogPost
from domain.repositories import IBlogPostRepository

from .models import BlogPostContentModel


class PostgresBlogPostRepository(IBlogPostRepository):
	"""Repository implementation for blog posts using PostgreSQL via SQLAlchemy AsyncSession."""

	def __init__(self, session: AsyncSession):
		self._session = session
		self._logger = getLogger(__name__)

	async def find_by_paper_id(self, paper_id: str) -> BlogPost | None:
		statement = select(BlogPostContentModel).where(
			col(BlogPostContentModel.paper_id) == paper_id
		)
		result = await self._session.execute(statement)
		row = result.scalars().first()
		if row is None:
			return None
		return BlogPost(
			id=row.id,
			paper_id=row.paper_id,
			content=row.content,
			created_at=row.created_at,
			updated_at=row.updated_at,
		)

	async def save(self, blog_post: BlogPost) -> BlogPost:
		statement = select(BlogPostContentModel).where(
			col(BlogPostContentModel.paper_id) == blog_post.paper_id
		)
		result = await self._session.execute(statement)
		existing = result.scalars().first()
		now = datetime.now(UTC)
		if existing is not None:
			existing.content = blog_post.content
			existing.updated_at = now
			await self._session.flush()
			return BlogPost(
				id=existing.id,
				paper_id=existing.paper_id,
				content=existing.content,
				created_at=existing.created_at,
				updated_at=existing.updated_at,
			)
		model = BlogPostContentModel(
			paper_id=blog_post.paper_id,
			content=blog_post.content,
			created_at=now,
			updated_at=now,
		)
		self._session.add(model)
		await self._session.flush()
		return BlogPost(
			id=model.id,
			paper_id=model.paper_id,
			content=model.content,
			created_at=model.created_at,
			updated_at=model.updated_at,
		)
