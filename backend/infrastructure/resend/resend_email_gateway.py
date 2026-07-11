import asyncio
import html

import resend
from resend.exceptions import ResendError

from domain.errors import EmailDeliveryError
from domain.gateways import DigestItem, IEmailGateway

from .config import ResendConfig, get_resend_config

_SUMMARY_MAX_CHARS = 200


class ResendEmailGateway(IEmailGateway):
	"""Sends emails via the official Resend Python SDK (sync SDK run in a worker thread)."""

	def __init__(self, config: ResendConfig | None = None) -> None:
		self._config = config or get_resend_config()
		resend.api_key = self._config.resend_api_key.get_secret_value()

	async def send_weekly_digest(self, to: str, items: list[DigestItem]) -> None:
		settings_url = f'{self._config.frontend_base_url}/settings/topics'
		cards = ''.join(self._render_card(item) for item in items)
		body = (
			'<div style="font-family:sans-serif;max-width:600px;margin:0 auto;color:#111">'
			'<h1 style="font-size:18px">今週のおすすめ論文</h1>'
			f'{cards}'
			'<p style="font-size:12px;color:#666;margin-top:24px">'
			f'配信を停止するには<a href="{settings_url}">設定ページ</a>から解除してください。'
			'</p></div>'
		)
		params: resend.Emails.SendParams = {
			'from': self._config.resend_from_address,
			'to': [to],
			'subject': f'今週の論文ダイジェスト（{len(items)}件）',
			'html': body,
			'headers': {'List-Unsubscribe': f'<{settings_url}>'},
		}
		try:
			await asyncio.to_thread(resend.Emails.send, params)
		except ResendError as e:
			raise EmailDeliveryError(str(e)) from e

	def _render_card(self, item: DigestItem) -> str:
		url = f'{self._config.frontend_base_url}/blog/{item.paper_id}'
		title = html.escape(item.title)
		summary = html.escape(item.summary[:_SUMMARY_MAX_CHARS])
		return (
			'<div style="border:1px solid #eee;border-radius:8px;padding:16px;margin:12px 0">'
			f'<a href="{url}" style="font-size:16px;font-weight:bold;color:#111;'
			f'text-decoration:none">{title}</a>'
			f'<p style="font-size:14px;color:#444;line-height:1.6">{summary}…</p>'
			f'<a href="{url}" style="font-size:14px;color:#2563eb">続きを読む →</a>'
			'</div>'
		)
