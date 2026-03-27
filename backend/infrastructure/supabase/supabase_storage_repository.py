from logging import getLogger

from domain.entities.latex_file import TranslatedLatexFile
from domain.repositories import IFileStorageRepository
from supabase import create_async_client


class SupabaseStorageRepository(IFileStorageRepository):
	"""Repository implementation using Supabase Storage."""

	def __init__(self, supabase_url: str, supabase_key: str, bucket_name: str):
		self._supabase_url = supabase_url
		self._supabase_key = supabase_key
		self._bucket_name = bucket_name
		self._logger = getLogger(__name__)

	async def save_translated_file_and_get_url(self, translated_file: TranslatedLatexFile) -> str:
		self._logger.info('Saving translated file %s', translated_file.storage_path)
		supabase = await create_async_client(self._supabase_url, self._supabase_key)
		with open(translated_file.path, 'rb') as f:
			await supabase.storage.from_(self._bucket_name).upload(
				translated_file.storage_path,
				file=f,
				file_options={
					'content-type': 'application/pdf',
					'cache-control': '3600',
					'x-upsert': 'true',
				},
			)
		self._logger.info('Saved translated file %s', translated_file.storage_path)
		response_url = await supabase.storage.from_(self._bucket_name).get_public_url(
			translated_file.storage_path
		)
		return response_url
