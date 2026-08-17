from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnthropicConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

	# 既定は Vertex 経由（既存 GCP アカウント/課金で Claude を呼ぶ）。別ベンダー契約・
	# 別請求を避けたい運用に合わせる。'api' にすると Anthropic 直 API（API キー）になる。
	anthropic_provider: Literal['vertex', 'api'] = Field(
		default='vertex',
		description="Claude backend: 'vertex' (GCP billing via ADC) or 'api' (Anthropic API key).",
	)
	anthropic_chat_model: str = Field(
		default='claude-haiku-4-5',
		description='Claude model id used for the paper chat. Switch to a stronger model '
		'(e.g. claude-sonnet-4-6) via env when higher reasoning is needed.',
	)

	# --- Vertex 利用時 ---
	gcp_project_id: str = Field(
		default='', description='GCP project id for Claude on Vertex AI (provider=vertex).'
	)
	vertex_region: str = Field(
		default='us-east5',
		description='Vertex AI region serving Claude (e.g. us-east5, europe-west1, global).',
	)

	# --- Anthropic 直 API 利用時 ---
	anthropic_api_key: SecretStr = Field(
		default=SecretStr(''), description='Anthropic API key (only used when provider=api).'
	)


@lru_cache
def get_anthropic_config() -> AnthropicConfig:
	return AnthropicConfig()
