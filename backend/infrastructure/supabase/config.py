from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from functools import lru_cache


class SupabaseConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	blog_figures_bucket_name: str = Field(
		default='blog-figures', description='The name of the bucket for blog figures'
	)
	translated_arxiv_bucket_name: str = Field(
		default='translated-arxiv-bucket', description='The name of the bucket for translated arXiv'
	)
	supabase_url: SecretStr = Field(
		default=SecretStr(''), description='The URL of the Supabase database'
	)
	supabase_api_key: SecretStr = Field(
		default=SecretStr(''), description='The API key for the Supabase database'
	)


@lru_cache
def get_supabase_config() -> SupabaseConfig:
	return SupabaseConfig()
