from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def create_async_session_factory(postgres_url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory from a PostgreSQL URL.

    Converts the URL scheme from postgresql:// or postgres:// to postgresql+asyncpg://
    if necessary.
    """
    if postgres_url.startswith('postgresql://'):
        async_url = postgres_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    elif postgres_url.startswith('postgres://'):
        async_url = postgres_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    else:
        async_url = postgres_url

    engine = create_async_engine(async_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Yield an AsyncSession that is committed on success and rolled back on failure."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
