from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from functools import lru_cache


class QdrantConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	qdrant_url: SecretStr = Field(
		default=SecretStr(''), description='The URL of the Qdrant database'
	)
	qdrant_api_key: SecretStr = Field(
		default=SecretStr(''), description='The API key for the Qdrant database'
	)
	figure_collection_name: str = Field(
		default='figures', description='The name of the collection for figures'
	)
	text_collection_name: str = Field(
		default='text_chunks', description='The name of the collection for text chunks'
	)


@lru_cache
def get_qdrant_config() -> QdrantConfig:
	return QdrantConfig()
