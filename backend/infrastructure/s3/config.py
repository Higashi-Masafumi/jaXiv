from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3StorageConfig(BaseSettings):
	"""Configuration for an S3-compatible object storage backend.

	Designed primarily for Cloudflare R2 (zero-egress, S3-compatible) but works
	with any S3-compatible provider (AWS S3, Backblaze B2, MinIO, ...) by only
	changing the endpoint and credentials. Objects are served to the public via
	a custom domain (or the ``r2.dev`` development URL), configured per bucket as
	a public base URL.
	"""

	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

	s3_endpoint_url: str = Field(
		default='',
		description=(
			'S3-compatible endpoint URL. For Cloudflare R2 this is '
			'https://<account_id>.r2.cloudflarestorage.com'
		),
	)
	s3_access_key_id: SecretStr = Field(
		default=SecretStr(''), description='Access key id for the S3-compatible endpoint'
	)
	s3_secret_access_key: SecretStr = Field(
		default=SecretStr(''), description='Secret access key for the S3-compatible endpoint'
	)
	s3_region: str = Field(default='auto', description="Region name. Cloudflare R2 expects 'auto'.")

	translated_arxiv_bucket_name: str = Field(
		default='translated-arxiv-bucket',
		description='The name of the bucket for translated arXiv PDFs',
	)
	blog_figures_bucket_name: str = Field(
		default='blog-figures', description='The name of the bucket for blog figures'
	)

	translated_arxiv_public_base_url: str = Field(
		default='',
		description=(
			'Public base URL that serves the translated-arxiv bucket '
			'(custom domain or r2.dev URL), e.g. https://pdf.example.com'
		),
	)
	blog_figures_public_base_url: str = Field(
		default='',
		description=(
			'Public base URL that serves the blog-figures bucket '
			'(custom domain or r2.dev URL), e.g. https://figures.example.com'
		),
	)


@lru_cache
def get_s3_storage_config() -> S3StorageConfig:
	return S3StorageConfig()
