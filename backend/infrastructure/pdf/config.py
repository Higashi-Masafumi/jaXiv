from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class PdfConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
	layout_analysis_url: str = Field(
		default='http://localhost:7860', description='The URL of the layout analysis service'
	)


@lru_cache
def get_pdf_config() -> PdfConfig:
	return PdfConfig()
