from contextlib import AbstractAsyncContextManager

import aioboto3
from types_aiobotocore_s3 import S3Client

from infrastructure.s3.config import S3StorageConfig


def create_s3_client(config: S3StorageConfig) -> AbstractAsyncContextManager[S3Client]:
	"""Return an async context manager yielding an S3-compatible client.

	Use it as ``async with create_s3_client(config) as s3: ...``.
	"""
	session = aioboto3.Session()
	return session.client(
		's3',
		endpoint_url=config.s3_endpoint_url,
		aws_access_key_id=config.s3_access_key_id.get_secret_value(),
		aws_secret_access_key=config.s3_secret_access_key.get_secret_value(),
		region_name=config.s3_region,
	)


def build_public_url(public_base_url: str, key: str) -> str:
	"""Join a public base URL and an object key into a public, browsable URL."""
	return f'{public_base_url.rstrip("/")}/{key.lstrip("/")}'


__all__ = ['S3Client', 'build_public_url', 'create_s3_client']
