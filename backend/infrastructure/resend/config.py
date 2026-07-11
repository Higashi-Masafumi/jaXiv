from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class ResendConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

	resend_api_key: SecretStr = Field(default=SecretStr(''), description='Resend API key')
	resend_from_address: str = Field(
		default='jaXiv <onboarding@resend.dev>',
		description='From header for digest emails',
	)
	frontend_base_url: str = Field(
		default='http://localhost:5173', description='Frontend base URL for links in emails'
	)

	@field_validator('frontend_base_url')
	@classmethod
	def strip_trailing_slash(cls, v: str) -> str:
		return v.rstrip('/')


def get_resend_config() -> ResendConfig:
	return ResendConfig()
