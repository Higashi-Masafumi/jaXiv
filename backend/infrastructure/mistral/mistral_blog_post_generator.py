import base64
import logging
import re
from logging import getLogger
from pathlib import Path
from typing import ClassVar, Final

from mistralai import Mistral
from mistralai.models.sdkerror import SDKError
from mistralai.types import UNSET, UNSET_SENTINEL
from pydantic import BaseModel, Field
from tenacity import (
	AsyncRetrying,
	before_sleep_log,
	retry_if_exception,
	stop_after_attempt,
	wait_exponential,
)

from domain.entities.arxiv import ArxivPaperMetadata
from domain.entities.figure import UploadedFigure
from domain.entities.pdf_paper import PdfPaperMetadata
from domain.gateways import IBlogPostGenerator, IPdfBlogPostGenerator
from infrastructure.mistral.config import get_mistral_config

mistral_config = get_mistral_config()


class PdfBlogResponse(BaseModel):
	"""Mistral structured output schema for PDF blog post generation."""

	title: str = Field(description='論文の英語原題')
	authors: list[str] = Field(description='著者名リスト（英語原文）')
	summary: str = Field(description='論文アブストラクトの要約（英語・2〜3文）')
	content: str = Field(description='日本語ブログ記事の Markdown 本文')


class MistralBlogPostGenerator(IBlogPostGenerator, IPdfBlogPostGenerator):
	"""Gateway implementation for generating blog posts using Mistral API.

	Recommended model: ``mistral-small-latest`` (Mistral Small 3.1)
	- Supports Document QnA (PDF via base64 / URL)
	- Free tier: 1B tokens / month
	- Context window: 128K tokens
	"""

	MARKDOWN_FENCE_RE: ClassVar[re.Pattern[str]] = re.compile(r'```markdown\s*([\s\S]*?)```')

	def __init__(
		self,
		api_key: str,
		model: str = 'mistral-small-latest',
		max_latex_chars: int = 80_000,
	):
		self._client = Mistral(api_key=mistral_config.mistral_api_key.get_secret_value())
		self._logger = getLogger(__name__)
		self._model: Final[str] = model
		self._max_latex_chars: Final[int] = max_latex_chars

	# ------------------------------------------------------------------
	# System prompts
	# ------------------------------------------------------------------

	@property
	def _system_prompt(self) -> str:
		return """\
あなたは学術論文を一般向け日本語ブログに変換する専門家です。
arXiv 論文情報をもとに Markdown 形式でブログ記事を執筆してください。

# 記事構成
1. タイトル（論文タイトルの日本語訳）
2. 概要（1〜2 段落）
3. 背景・問題設定
4. 提案手法
5. 実験・結果
6. 考察・まとめ

# 図の挿入（必須）
「利用可能な図」に挙げられた図は、論文の要点を説明する箇所に積極的に挿入すること。
図を挿入する際は以下の **2行セット** を厳守すること：

```
![Figure N: 内容の簡潔な説明](IMG_N)
*Figure N: 何を示しているかの日本語説明*
```

- `IMG_N` は「利用可能な図」に記載されたキーを一字一句そのまま使うこと
- 画像行の直後に `*...*` でキャプションを付けること（Zenn のキャプション記法）
- 「IMG_N を参照」などインライン参照は禁止

# Markdown・出力ルール
- セクションヘッダは `##` から（`#` はタイトル用）
- 改行は実際の改行文字を使うこと（`\\n` という文字列を出力してはならない）
- 出力全体を ```markdown ``` ブロックで囲むこと
- 専門用語は初出時に簡単な説明を加えること

# 数式ルール（KaTeX）
- インライン: `$...$` / ブロック: `$$...$$`（前後に空行必須）
- `\\newcommand`/`\\def` のカスタムマクロは標準 KaTeX コマンドに展開すること
- 旧式コマンド（`\\tt`/`\\bf`/`\\it`/`\\rm` 等）禁止 → `\\texttt{}`/`\\textbf{}`/`\\textit{}`/`\\textrm{}`
- 数式中のテキストは `\\text{}` を使用（`\\mbox{}` 禁止）
- `\\label{}`/`\\ref{}` は使わず文脈で説明すること
"""

	@property
	def _pdf_system_prompt(self) -> str:
		return """\
あなたは学術論文を一般向け日本語ブログに変換する専門家です。
添付 PDF を読み、JSON でメタデータとブログ記事を返してください。

# 返すべきフィールド
- title: 論文の英語原題（PDF から正確に読み取ること）
- authors: 著者名リスト（英語原文）
- summary: アブストラクトの要約（英語・2〜3文）
- content: 一般読者向け日本語ブログ記事（Markdown 形式）

# content の構成
1. タイトル（日本語訳）
2. 概要（1〜2 段落）
3. 背景・問題設定
4. 提案手法
5. 実験・結果
6. 考察・まとめ

# 図の挿入（必須）
「利用可能な図」に列挙された図はすべて記事中に挿入すること。図を省略した解説は不完全とみなす。
図を挿入する際は以下の **2行セット** を厳守すること：

```
![Figure N: 内容の簡潔な説明](IMG_N)
*Figure N: 何を示しているかの日本語説明*
```

- `IMG_N` は「利用可能な図」に記載されたキーを一字一句そのまま使うこと
- 画像行の直後に `*...*` でキャプションを付けること（Zenn のキャプション記法）
- 「IMG_N を参照」などインライン参照は禁止

# Markdown・出力ルール
- セクションヘッダは `##` から（`#` はタイトル用）
- 専門用語は初出時に簡単な説明を加えること

# 数式ルール（KaTeX）
- インライン: `$...$` / ブロック: `$$...$$`（前後に空行必須）
- `\\newcommand`/`\\def` のカスタムマクロは標準 KaTeX コマンドに展開すること
- 旧式コマンド（`\\tt`/`\\bf`/`\\it`/`\\rm` 等）禁止 → `\\texttt{}`/`\\textbf{}`/`\\textit{}`/`\\textrm{}`
- 数式中のテキストは `\\text{}` を使用（`\\mbox{}` 禁止）
- `\\label{}`/`\\ref{}` は使わず文脈で説明すること
"""

	# ------------------------------------------------------------------
	# IBlogPostGenerator
	# ------------------------------------------------------------------

	async def generate(
		self,
		paper_metadata: ArxivPaperMetadata,
		latex_source_dir: Path,
		figure_urls: dict[str, str],
	) -> str:
		tex_parts: list[str] = []
		total = 0
		for tex_file in sorted(latex_source_dir.rglob('*.tex')):
			try:
				text = tex_file.read_text(encoding='utf-8', errors='ignore')
				if total + len(text) > self._max_latex_chars:
					tex_parts.append(text[: self._max_latex_chars - total])
					break
				tex_parts.append(text)
				total += len(text)
			except Exception:
				self._logger.warning('Failed to read %s', tex_file, exc_info=True)
		latex_content = '\n\n'.join(tex_parts)

		figure_section = ''
		placeholder_map: dict[str, str] = {}
		if figure_urls:
			lines = ['# 利用可能な図\n']
			for i, (filename, url) in enumerate(figure_urls.items(), 1):
				placeholder = f'IMG_{i}'
				placeholder_map[placeholder] = url
				lines.append(f'- {filename}: {placeholder}')
			lines.append('')
			figure_section = '\n'.join(lines)

		authors_str = ', '.join(a.name for a in paper_metadata.authors)
		user_prompt = (
			f'# 論文情報\n'
			f'- タイトル: {paper_metadata.title}\n'
			f'- 著者: {authors_str}\n'
			f'- arXiv ID: {paper_metadata.paper_id.root}\n'
			f'- 概要:\n{paper_metadata.summary}\n\n'
			f'{figure_section}'
			f'# LaTeX ソースコード（抜粋）\n'
			f'```latex\n{latex_content}\n```\n\n'
			'上記の情報をもとに、日本語のブログ記事を Markdown 形式で作成してください。'
		)

		self._logger.info('Generating blog post for paper %s', paper_metadata.paper_id.root)
		response = await self._chat_with_retry(
			messages=[
				{'role': 'system', 'content': self._system_prompt},
				{'role': 'user', 'content': user_prompt},
			],
		)

		message_content = response.choices[0].message.content
		if message_content is None or message_content in (UNSET, UNSET_SENTINEL):
			raw_text = ''
		elif isinstance(message_content, list):
			raw_text = ''.join(str(c) for c in message_content)
		else:
			raw_text = str(message_content)
		content = self._extract_markdown(raw_text)
		return self._replace_placeholders(content, placeholder_map)

	# ------------------------------------------------------------------
	# IPdfBlogPostGenerator
	# ------------------------------------------------------------------

	async def generate_from_pdf(
		self,
		pdf_path: Path,
		figures: list[UploadedFigure],
	) -> tuple[PdfPaperMetadata, str]:
		figure_section = ''
		placeholder_map: dict[str, str] = {}
		if figures:
			lines = ['# 利用可能な図\n']
			for i, fig in enumerate(figures, 1):
				placeholder = f'IMG_{i}'
				placeholder_map[placeholder] = fig.url
				label = (
					f'Figure {fig.figure_number}'
					if fig.figure_number
					else f'図 (p.{fig.page_number})'
				)
				caption_part = f' "{fig.caption}"' if fig.caption else ''
				lines.append(f'- {label} p.{fig.page_number}{caption_part}: {placeholder}')
			lines.append('')
			figure_section = '\n'.join(lines)

		user_text = (
			f'{figure_section}'
			'添付の PDF 論文を読み、メタデータ（title, authors, summary）と日本語ブログ記事（content）を'
			'次の JSON スキーマに従って返してください。\n\n'
			f'```json\n{PdfBlogResponse.model_json_schema()}\n```'
		)

		pdf_bytes = pdf_path.read_bytes()
		b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
		self._logger.info('Sending PDF to Mistral: %s (%d bytes)', pdf_path.name, len(pdf_bytes))

		response = await self._chat_with_retry(
			messages=[
				{'role': 'system', 'content': self._pdf_system_prompt},
				{
					'role': 'user',
					'content': [
						{
							'type': 'document_url',
							'document_url': f'data:application/pdf;base64,{b64_pdf}',
						},
						{
							'type': 'text',
							'text': user_text,
						},
					],
				},
			],
			response_format={'type': 'json_object'},
		)

		message_content = response.choices[0].message.content
		if message_content is None or message_content in (UNSET, UNSET_SENTINEL):
			raw_text = '{}'
		elif isinstance(message_content, list):
			raw_text = ''.join(str(c) for c in message_content) or '{}'
		else:
			raw_text = str(message_content) or '{}'
		parsed = PdfBlogResponse.model_validate_json(raw_text)
		metadata = PdfPaperMetadata(
			title=parsed.title,
			authors=parsed.authors,
			summary=parsed.summary,
		)
		content = self._normalize_literal_newlines(parsed.content)
		content = self._ensure_math_blank_lines(content)
		return metadata, self._replace_placeholders(content, placeholder_map)

	# ------------------------------------------------------------------
	# Retry helper
	# ------------------------------------------------------------------

	async def _chat_with_retry(self, **kwargs: object):
		"""Call chat.complete_async with exponential backoff on 5xx errors."""
		async for attempt in AsyncRetrying(
			retry=retry_if_exception(
				lambda exc: isinstance(exc, SDKError) and exc.status_code >= 500
			),
			stop=stop_after_attempt(5),
			wait=wait_exponential(multiplier=1, min=2, max=16),
			before_sleep=before_sleep_log(self._logger, logging.WARNING),
			reraise=True,
		):
			with attempt:
				return await self._client.chat.complete_async(
					model=self._model,
					**kwargs,  # type: ignore[arg-type]
				)
		raise RuntimeError('Unreachable')  # pragma: no cover

	# ------------------------------------------------------------------
	# Post-processing helpers (identical to GeminiBlogPostGenerator)
	# ------------------------------------------------------------------

	@staticmethod
	def _replace_placeholders(content: str, placeholder_map: dict[str, str]) -> str:
		for placeholder, url in sorted(
			placeholder_map.items(), key=lambda x: len(x[0]), reverse=True
		):
			content = content.replace(placeholder, url)
		return content

	def _extract_markdown(self, raw_text: str) -> str:
		match = self.MARKDOWN_FENCE_RE.search(raw_text)
		if match:
			content = match.group(1).strip()
		else:
			content = re.sub(r'^```[a-z]*\n', '', raw_text.strip())
			content = re.sub(r'\n```$', '', content)
			content = content.strip()
		return self._ensure_math_blank_lines(content)

	@staticmethod
	def _normalize_literal_newlines(content: str) -> str:
		"""Replace literal \\n newline artifacts with actual newlines.

		Targets only \\n NOT followed by a letter, so LaTeX commands such as
		\\nabla, \\neq, \\nu are left intact.  The artifact arises when a
		JSON-mode LLM response double-escapes newlines (\\\\n → \\n after
		JSON parsing).
		"""
		return re.sub(r'\\n(?![a-zA-Z])', '\n', content)

	@staticmethod
	def _ensure_math_blank_lines(content: str) -> str:
		"""$$ の前後に空行を確保（zenn-markdown-html がブロック数式として認識するために必須）。"""
		lines = content.split('\n')
		result: list[str] = []
		in_math = False
		for line in lines:
			stripped = line.strip()
			if stripped == '$$':
				if not in_math:
					if result and result[-1].strip() != '':
						result.append('')
					in_math = True
				else:
					in_math = False
				result.append(line)
			else:
				if not in_math and result and result[-1].strip() == '$$' and stripped != '':
					result.append('')
				result.append(line)
		return '\n'.join(result)
