from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import StrictStr, Field
from functools import lru_cache


class AuthConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	jwks_url: StrictStr = Field(default='', description='The URL of the JWKs endpoint')


@lru_cache
def get_auth_config() -> AuthConfig:
	return AuthConfig()
