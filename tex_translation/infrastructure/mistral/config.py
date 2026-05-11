from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MistralConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    mistral_api_key: SecretStr = Field(
        default=SecretStr(""), description="The API key for the Mistral API"
    )


@lru_cache
def get_mistral_config() -> MistralConfig:
    return MistralConfig()
