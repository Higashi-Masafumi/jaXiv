from logging import getLogger

from domain.repositories import IFileStorageRepository
from infrastructure.s3.client import build_public_url, create_s3_client
from infrastructure.s3.config import get_s3_storage_config


class S3StorageRepository(IFileStorageRepository):
	"""Repository implementation using an S3-compatible object store (e.g. Cloudflare R2)."""

	def __init__(self):
		self._config = get_s3_storage_config()
		self._bucket_name = self._config.translated_arxiv_bucket_name
		self._public_base_url = self._config.translated_arxiv_public_base_url
		self._logger = getLogger(__name__)

	async def save_translated_file_and_get_url(
		self,
		storage_path: str,
		content: bytes,
	) -> str:
		self._logger.info('Saving translated file %s', storage_path)
		async with create_s3_client(self._config) as s3:
			await s3.put_object(
				Bucket=self._bucket_name,
				Key=storage_path,
				Body=content,
				ContentType='application/pdf',
				CacheControl='3600',
			)
		public_url = build_public_url(self._public_base_url, storage_path)
		self._logger.info('Saved translated file %s → %s', storage_path, public_url)
		return public_url
