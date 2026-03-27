import re
from logging import getLogger
from pathlib import Path

from google import genai
from google.genai import types

from domain.entities.arxiv import ArxivPaperMetadata
from domain.gateways import IBlogPostGenerator

_SYSTEM_PROMPT = """\
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
- 図が提供されている場合は、適切な位置に `![図の説明](URL)` として埋め込んでください
- 画像URL（png/jpg/webp/svg など）のみ `![...]` で埋め込み、PDF URL は `[図の説明](URL)` の通常リンクにしてください
- 数式は LaTeX 記法（`$...$` や `$$...$$`）のままで構いません
- 専門用語は初出時に簡単な説明を加えてください
- 出力は Markdown コードブロック（```markdown ... ```）で囲んでください
"""


class GeminiBlogPostGenerator(IBlogPostGenerator):
	"""Gateway implementation for generating blog posts using Gemini API."""

	def __init__(self, api_key: str):
		self._client = genai.Client(api_key=api_key)
		self._logger = getLogger(__name__)

	async def generate(
		self,
		paper_metadata: ArxivPaperMetadata,
		latex_source_dir: Path,
		figure_urls: dict[str, str],
	) -> str:
		latex_content = self._read_latex_content(latex_source_dir)
		authors_str = ', '.join(a.name for a in paper_metadata.authors)
		figure_section = self._build_figure_section(figure_urls)

		user_prompt = (
			f'# 論文情報\n'
			f'- タイトル: {paper_metadata.title}\n'
			f'- 著者: {authors_str}\n'
			f'- arXiv ID: {paper_metadata.paper_id.value}\n'
			f'- 概要:\n{paper_metadata.summary}\n\n'
			f'{figure_section}'
			f'# LaTeX ソースコード（抜粋）\n'
			f'```latex\n{latex_content}\n```\n\n'
			'上記の情報をもとに、日本語のブログ記事を Markdown 形式で作成してください。'
		)

		self._logger.info('Generating blog post for paper %s', paper_metadata.paper_id.value)
		response = self._client.models.generate_content(
			model='gemini-2.5-flash',
			config=types.GenerateContentConfig(
				system_instruction=_SYSTEM_PROMPT,
			),
			contents=user_prompt,
		)

		raw_text = response.text or ''
		return self._extract_markdown(raw_text)

	def _read_latex_content(self, source_dir: Path, max_chars: int = 80_000) -> str:
		"""Read and concatenate .tex files from the source directory (up to max_chars)."""
		tex_files = sorted(source_dir.rglob('*.tex'))
		parts: list[str] = []
		total = 0
		for tex_file in tex_files:
			try:
				text = tex_file.read_text(encoding='utf-8', errors='ignore')
				if total + len(text) > max_chars:
					parts.append(text[: max_chars - total])
					break
				parts.append(text)
				total += len(text)
			except Exception:
				self._logger.warning('Failed to read %s', tex_file, exc_info=True)
		return '\n\n'.join(parts)

	@staticmethod
	def _build_figure_section(figure_urls: dict[str, str]) -> str:
		if not figure_urls:
			return ''
		lines = ['# 利用可能な図のURL\n']
		for filename, url in figure_urls.items():
			lines.append(f'- {filename}: {url}')
		lines.append('\n')
		return '\n'.join(lines)

	@staticmethod
	def _extract_markdown(text: str) -> str:
		"""Extract content from ```markdown ... ``` fences if present."""
		match = re.search(r'```markdown\s*([\s\S]*?)```', text)
		if match:
			return match.group(1).strip()
		# Fallback: strip any outer ``` fences
		text = re.sub(r'^```[a-z]*\n', '', text.strip())
		text = re.sub(r'\n```$', '', text)
		return text.strip()
