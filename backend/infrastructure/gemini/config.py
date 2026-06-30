from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from functools import lru_cache


class GeminiConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	gemini_api_key: SecretStr = Field(
		default=SecretStr(''), description='The API key for the Gemini API'
	)
	blog_model: str = Field(
		default='gemini-3-flash-preview',
		description='Model used for blog post generation (override via GEMINI_BLOG_MODEL)',
		alias='GEMINI_BLOG_MODEL',
	)


@lru_cache
def get_gemini_config() -> GeminiConfig:
	return GeminiConfig()
