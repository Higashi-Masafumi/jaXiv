from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories import IAuthUserRepository
from domain.value_objects.user_id import UserId


class PostgresAuthUserRepository(IAuthUserRepository):
	"""Reads user email from Supabase's ``auth.users`` table.

	Requires the backend's DB role to have SELECT on the ``auth`` schema. Supabase's
	``postgres`` / ``service_role`` roles do (the same privileged connection that lets
	the backend bypass RLS for blog writes), so this works with the app's connection.
	"""

	def __init__(self, session: AsyncSession):
		self._session = session

	async def find_email(self, user_id: UserId) -> str | None:
		result = await self._session.execute(
			text('SELECT email FROM auth.users WHERE id = :id'),
			{'id': str(user_id.root)},
		)
		row = result.first()
		return row[0] if row is not None else None
