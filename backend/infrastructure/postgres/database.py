from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_postgres_config

config = get_postgres_config()


def create_async_session_factory() -> async_sessionmaker[AsyncSession]:
	"""Create an async session factory from a PostgreSQL URL."""
	postgres_url = config.postgres_url
	if postgres_url.startswith('postgresql://'):
		postgres_url = postgres_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
	elif postgres_url.startswith('postgres://'):
		postgres_url = postgres_url.replace('postgres://', 'postgresql+asyncpg://', 1)

	engine = create_async_engine(postgres_url, echo=False)
	return async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
	"""Yield an AsyncSession that is committed on success and rolled back on failure."""
	session_factory = create_async_session_factory()
	async with session_factory() as session:
		try:
			yield session
			await session.commit()
		except Exception:
			await session.rollback()
			raise
