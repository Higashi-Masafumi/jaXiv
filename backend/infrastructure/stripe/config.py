from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class StripeConfig(BaseSettings):
	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

	stripe_api_key: str = Field(default='', description='Stripe secret API key')
	stripe_webhook_secret: str = Field(
		default='', description='Webhook signing secret used to verify events'
	)
	stripe_price_id_paid: str = Field(
		default='', description='Stripe Price ID for the PAID subscription plan'
	)


def get_stripe_config() -> StripeConfig:
	return StripeConfig()
