from abc import ABC
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlAlchemyUnitOfWorkBase(ABC):
	def __init__(
		self,
		session_factory: async_sessionmaker[AsyncSession],
	):
		self._session_factory = session_factory
		self._session: AsyncSession

	async def __aenter__(self) -> Self:
		self._session = self._session_factory()
		return self

	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc_value: BaseException | None,
		traceback: TracebackType | None,
	) -> None:
		if exc_type is not None:
			await self._session.rollback()
		else:
			await self._session.commit()
		await self._session.close()
