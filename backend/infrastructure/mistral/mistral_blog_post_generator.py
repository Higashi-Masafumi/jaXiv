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
from tenacity import AsyncRetrying, before_sleep_log, retry_if_exception, stop_after_attempt, wait_exponential

from domain.entities.arxiv import ArxivPaperMetadata
from domain.entities.figure import UploadedFigure
from domain.entities.pdf_paper import PdfPaperMetadata
from domain.gateways import IBlogPostGenerator, IPdfBlogPostGenerator


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
        self._client = Mistral(api_key=api_key)
        self._logger = getLogger(__name__)
        self._model: Final[str] = model
        self._max_latex_chars: Final[int] = max_latex_chars

    # ------------------------------------------------------------------
    # System prompts
    # ------------------------------------------------------------------

    @property
    def _system_prompt(self) -> str:
        return """\
あなたは、学術論文を分かりやすいブログ記事に変換する専門家です。
与えられた arXiv 論文の情報をもとに、一般の読者にも理解しやすい日本語のブログ記事を Markdown 形式で執筆してください。

# ブログ記事の構成
1. タイトル（論文タイトルの日本語訳）
2. 概要（1〜2 段落で論文の要点を簡潔に説明）
3. 背景・問題設定（この研究が解こうとしている問題と、その重要性）
4. 提案手法（どのようなアプローチで問題を解いたか）
5. 実験・結果（どのような実験を行い、どのような結果が得られたか）
6. 考察・まとめ（研究の意義・限界・今後の展望）

# 注意事項
- Markdown のセクションヘッダは `##` から使用してください（`#` はタイトル用）
- 図を参照する際は必ず Markdown 画像記法 `![説明](IMG_N)` として独立した行で埋め込む。IMG_N は「利用可能な図」に列挙されたキー文字列を一字一句そのまま使うこと
  - 正しい例: `![Figure 2: 提案手法の概要](IMG_2)`
  - 禁止: `（IMG_N を参照）` `（URL を参照）` など、本文中にインラインで URL や IMG_N を埋め込むこと
- 数式は KaTeX 互換の LaTeX 記法で記述してください。以下のルールを厳守すること：
- インライン数式は `$...$`、ブロック数式は `$$...$$` で囲む
- ブロック数式の `$$` の前後には必ず空行を入れること（Markdown パーサがブロックとして認識するために必須）。例：
    ```
    テキスト

    $$
    E = mc^2
    $$

    テキスト
    ```
- `$` や `$$` の内側にさらに `$` を入れないこと（ネスト禁止）
- 論文ソース中の `\\newcommand` / `\\def` で定義されたカスタムマクロは絶対にそのまま使わず、標準的な KaTeX コマンドに展開すること。例：
    - `\\E` → `\\mathbb{E}`, `\\x` → `\\mathbf{x}`, `\\R` → `\\mathbb{R}` など
    - `\\TurboQuant` のような独自命名はプレーンテキストに置き換える
    - `\\left< \\right>` → `\\left\\langle \\right\\rangle`
- 旧式フォントコマンド（`\\tt`, `\\bf`, `\\it`, `\\rm`, `\\sf`, `\\sc`）は使用禁止。代わりに以下を使う：
    - `\\tt` → `\\texttt{}` または数式中なら `\\mathtt{}`
    - `\\bf` → `\\textbf{}` または `\\mathbf{}`
    - `\\it` → `\\textit{}` または `\\mathit{}`
    - `\\rm` → `\\textrm{}` または `\\mathrm{}`
- 数式中にテキストを入れる場合は `\\text{}` を使用（`\\mbox{}` や `\\hbox{}` は不可）
- KaTeX 非対応のコマンド例：`\\newcommand`, `\\def`, `\\DeclareMathOperator`, `\\usepackage`, `\\eqref`（`\\ref` を使う）
- `aligned`, `cases`, `matrix`, `bmatrix`, `pmatrix` 等の基本環境は使用可能
- `\\label{}` と `\\ref{}` はブログ記事では使わず、文脈で説明すること
- 専門用語は初出時に簡単な説明を加えてください
- 出力は Markdown コードブロック（```markdown ... ```）で囲んでください
"""

    @property
    def _pdf_system_prompt(self) -> str:
        return """\
あなたは、学術論文を分かりやすいブログ記事に変換する専門家です。
添付された PDF 論文を読み、JSON でメタデータとブログ記事を返してください。

# 返すべきフィールド
- title: 論文の英語原題（PDF から正確に読み取ること）
- authors: 著者名のリスト（英語原文）
- summary: アブストラクトの要約（英語・2〜3文）
- content: 一般読者向けの日本語ブログ記事（Markdown 形式）

# content（ブログ記事）の構成
1. タイトル（論文タイトルの日本語訳）
2. 概要（1〜2 段落で論文の要点を簡潔に説明）
3. 背景・問題設定（この研究が解こうとしている問題と、その重要性）
4. 提案手法（どのようなアプローチで問題を解いたか）
5. 実験・結果（どのような実験を行い、どのような結果が得られたか）
6. 考察・まとめ（研究の意義・限界・今後の展望）

# content の Markdown 注意事項
- セクションヘッダは `##` から使用（`#` はタイトル用）
- 図を参照する際は必ず Markdown 画像記法 `![説明](IMG_N)` として独立した行で埋め込む。IMG_N は「利用可能な図」に列挙されたキー文字列を一字一句そのまま使うこと
  - 正しい例: `![Figure 4: KVキャッシュのサイズ比較](IMG_4)`
  - 禁止: `（IMG_N を参照）` `（URL を参照）` など、本文中にインラインで URL や IMG_N を埋め込むこと
- 数式は KaTeX 互換の LaTeX 記法で記述。以下のルールを厳守：
  - インライン数式: `$...$`、ブロック数式: `$$...$$`
  - ブロック数式の `$$` 前後には必ず空行を入れること
  - `$` / `$$` のネスト禁止
  - `\\newcommand` / `\\def` で定義されたカスタムマクロは標準 KaTeX コマンドに展開する
  - 旧式フォントコマンド（`\\tt`, `\\bf`, `\\it`, `\\rm`）は使用禁止
  - `\\text{}` を使用（`\\mbox{}` / `\\hbox{}` 不可）
  - `\\label{}` / `\\ref{}` は使わず文脈で説明
- 専門用語は初出時に簡単な説明を加える
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
        content = self._ensure_math_blank_lines(parsed.content)
        return metadata, self._replace_placeholders(content, placeholder_map)

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    async def _chat_with_retry(self, **kwargs: object):
        """Call chat.complete_async with exponential backoff on 5xx errors."""
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(lambda exc: isinstance(exc, SDKError) and exc.status_code >= 500),
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
        for placeholder, url in sorted(placeholder_map.items(), key=lambda x: len(x[0]), reverse=True):
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
