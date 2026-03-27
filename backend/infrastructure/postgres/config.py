import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class PostgresConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	postgres_url: str = Field(
		...,
		description='The URL of the PostgreSQL database',
	)


def get_postgres_config() -> PostgresConfig:
	return PostgresConfig(postgres_url=os.getenv('POSTGRES_URL', ''))
