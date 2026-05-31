import logging
from logging import getLogger
from typing import Final

from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field
from tenacity import (
	before_sleep_log,
	retry,
	retry_if_exception_type,
	stop_after_attempt,
	wait_exponential,
)

from domain.gateways import IFigureQueryGenerator
from infrastructure.gemini.config import get_gemini_config

logger = getLogger(__name__)


class FigureQueriesResponse(BaseModel):
	"""Gemini structured output schema for figure search query generation."""

	queries: list[str] = Field(
		description='図検索用の英語クエリ（多様な観点・短い名詞句）',
	)


gemini_config = get_gemini_config()


class GeminiFigureQueryGenerator(IFigureQueryGenerator):
	"""Gateway implementation that expands a user description into search queries.

	Given a Japanese/English description of the research content or the figure
	the user wants to create, Gemini emits several diverse English queries that
	work well against the caption vectors (nomic-embed-text) of the figure
	collection.
	"""

	def __init__(self, model: str = 'gemini-2.5-flash'):
		self.client = genai.Client(api_key=gemini_config.gemini_api_key.get_secret_value())
		self.model: Final[str] = model

	@property
	def system_prompt(self) -> str:
		return """\
あなたは学術論文の図を検索するための検索クエリを設計する専門家です。
ユーザーが「これから作りたい図」や「自分の研究内容」を説明します。
その内容を参考にできる既存論文の図を見つけるための検索クエリを生成してください。

# ルール
- クエリは **英語の短い名詞句** で出力すること（図のキャプションのベクトル検索に最適化）
- アーキテクチャ図・手法概要図・結果プロット・アブレーション表・データフロー図など、
  **多様な観点** からクエリを作ること
- 各クエリは具体的な図の種類や内容を表すこと（例: "transformer architecture diagram",
  "reinforcement learning reward curve", "ablation study results table"）
- 抽象的すぎる単語のみ（例: "figure", "diagram"）は避けること
- 指定された個数だけ生成すること
"""

	@retry(
		retry=retry_if_exception_type(genai_errors.ServerError),
		stop=stop_after_attempt(5),
		wait=wait_exponential(multiplier=1, min=2, max=16),
		before_sleep=before_sleep_log(logger, logging.WARNING),
		reraise=True,
	)
	async def generate_queries(self, user_input: str, n: int = 4) -> list[str]:
		user_prompt = (
			f'# ユーザーの入力\n{user_input}\n\n'
			f'上記の内容を参考にできる図を探すための検索クエリを {n} 個生成してください。'
		)
		logger.info('Generating %d figure search queries with %s', n, self.model)
		response = await self.client.aio.models.generate_content(
			model=self.model,
			config={
				'system_instruction': self.system_prompt,
				'response_mime_type': 'application/json',
				'response_json_schema': FigureQueriesResponse.model_json_schema(),
			},
			contents=user_prompt,
		)
		parsed = FigureQueriesResponse.model_validate_json(response.text or '{}')
		# Dedupe while preserving order, drop blanks, and cap at ``n``.
		seen: set[str] = set()
		queries: list[str] = []
		for raw in parsed.queries:
			query = raw.strip()
			if query and query.lower() not in seen:
				seen.add(query.lower())
				queries.append(query)
		return queries[:n]
