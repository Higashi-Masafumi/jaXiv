from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TexTranslationConfig(BaseSettings):
	model_config = SettingsConfigDict(
		env_file='.env', env_file_encoding='utf-8', extra='ignore'
	)
	tex_translation_url: str = Field(
		default='http://localhost:8100',
		description='Base URL of the tex_translation microservice',
	)
	tex_translation_timeout_seconds: float = Field(
		default=600.0,
		description='Request timeout for tex_translation (translation+compile can be slow)',
	)


@lru_cache
def get_tex_translation_config() -> TexTranslationConfig:
	return TexTranslationConfig()
