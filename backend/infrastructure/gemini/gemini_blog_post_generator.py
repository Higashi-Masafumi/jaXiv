import re
from logging import getLogger
from pathlib import Path
from typing import ClassVar, Final

from google import genai
from google.genai import types

from domain.entities.arxiv import ArxivPaperMetadata
from domain.gateways import IBlogPostGenerator


class GeminiBlogPostGenerator(IBlogPostGenerator):
	"""Gateway implementation for generating blog posts using Gemini API."""

	MARKDOWN_FENCE_RE: ClassVar[re.Pattern[str]] = re.compile(r'```markdown\s*([\s\S]*?)```')

	def __init__(
		self,
		api_key: str,
		model: str = 'gemini-2.5-flash',
		max_latex_chars: int = 80_000,
	):
		self.client = genai.Client(api_key=api_key)
		self.logger = getLogger(__name__)
		self.model: Final[str] = model
		self.max_latex_chars: Final[int] = max_latex_chars

	@property
	def system_prompt(self) -> str:
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
		- 図が提供されている場合は、適切な位置に `![図の説明](URL)` として埋め込んでください
		- 画像URL（png/jpg/webp/svg など）のみ `![...]` で埋め込み、PDF URL は `[図の説明](URL)` の通常リンクにしてください
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

	async def generate(
		self,
		paper_metadata: ArxivPaperMetadata,
		latex_source_dir: Path,
		figure_urls: dict[str, str],
	) -> str:
		# LaTeX ソース読み込み
		tex_parts: list[str] = []
		total = 0
		for tex_file in sorted(latex_source_dir.rglob('*.tex')):
			try:
				text = tex_file.read_text(encoding='utf-8', errors='ignore')
				if total + len(text) > self.max_latex_chars:
					tex_parts.append(text[: self.max_latex_chars - total])
					break
				tex_parts.append(text)
				total += len(text)
			except Exception:
				self.logger.warning('Failed to read %s', tex_file, exc_info=True)
		latex_content = '\n\n'.join(tex_parts)

		# 図URL一覧セクション
		figure_section = ''
		if figure_urls:
			lines = ['# 利用可能な図のURL\n']
			for filename, url in figure_urls.items():
				lines.append(f'- {filename}: {url}')
			lines.append('\n')
			figure_section = '\n'.join(lines)

		authors_str = ', '.join(a.name for a in paper_metadata.authors)
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

		self.logger.info('Generating blog post for paper %s', paper_metadata.paper_id.value)
		response = await self.client.aio.models.generate_content(
			model=self.model,
			config=types.GenerateContentConfig(
				system_instruction=self.system_prompt,
			),
			contents=user_prompt,
		)

		# Markdown 抽出
		raw_text = response.text or ''
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
					# 開始 $$: 直前が空行でなければ空行を挿入
					if result and result[-1].strip() != '':
						result.append('')
					in_math = True
				else:
					# 終了 $$: そのまま追加（後続行の処理で空行を挿入）
					in_math = False
				result.append(line)
			else:
				# 終了 $$ の直後に非空行が来たら空行を挿入
				if not in_math and result and result[-1].strip() == '$$' and stripped != '':
					result.append('')
				result.append(line)
		return '\n'.join(result)
