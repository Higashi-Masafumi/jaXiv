from logging import getLogger

from supabase import create_async_client

from domain.repositories import IFileStorageRepository
from infrastructure.supabase.config import get_supabase_config

supabase_config = get_supabase_config()


class SupabaseStorageRepository(IFileStorageRepository):
	"""Repository implementation using Supabase Storage."""

	def __init__(self):
		self._supabase_url = supabase_config.supabase_url.get_secret_value()
		self._supabase_key = supabase_config.supabase_api_key.get_secret_value()
		self._bucket_name = supabase_config.translated_arxiv_bucket_name
		self._logger = getLogger(__name__)

	async def save_translated_file_and_get_url(
		self,
		storage_path: str,
		content: bytes,
	) -> str:
		self._logger.info('Saving translated file %s', storage_path)
		supabase = await create_async_client(self._supabase_url, self._supabase_key)
		await supabase.storage.from_(self._bucket_name).upload(
			storage_path,
			file=content,
			file_options={
				'content-type': 'application/pdf',
				'cache-control': '3600',
				'x-upsert': 'true',
			},
		)
		self._logger.info('Saved translated file %s', storage_path)
		response_url = await supabase.storage.from_(self._bucket_name).get_public_url(
			storage_path
		)
		return response_url
