"""LaTeX source preprocessing for blog generation.

arXiv papers are distributed as LaTeX source (e-print), which is far more
reliable than PDF/OCR for preserving structure, equations and figures.  But
feeding the raw source to an LLM has three failure modes that this module
fixes:

1. Multi-file papers split across ``\\input``/``\\include`` must be assembled
   in document order — globbing ``*.tex`` alphabetically scrambles structure
   and can truncate the body to leave only an appendix.
2. Author-defined macros (``\\newcommand``/``\\def`` …) must be visible and
   intact, otherwise the LLM "mentally expands" them and corrupts the math.
3. ``%`` comments are noise that confuses generation.

The public entry point is :meth:`LatexPreprocessor.assemble`.
"""

import re
from logging import getLogger
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field

# \input{file}, \include{file}, \subfile{file} (optional .tex extension)
_INCLUDE_RE: Final[re.Pattern[str]] = re.compile(r'\\(?:input|include|subfile)\s*\{([^}]+)\}')
# Author-defined macros worth surfacing to the LLM verbatim.
_MACRO_RE: Final[re.Pattern[str]] = re.compile(
	r'^\s*\\(?:newcommand|renewcommand|providecommand|def|let'
	r'|DeclareMathOperator|newenvironment)\*?\b'
)
# An unescaped % starts a comment that runs to end of line.
_COMMENT_RE: Final[re.Pattern[str]] = re.compile(r'(?<!\\)%.*')

_MAX_INCLUDE_DEPTH: Final[int] = 16


class AssembledLatex(BaseModel):
	"""Result of assembling a paper's LaTeX source."""

	body: str = Field(description='ドキュメント順に結合・整形した LaTeX 本文')
	macros: list[str] = Field(
		default_factory=list,
		description='著者定義マクロ（\\newcommand/\\def 等）の定義行',
	)


class LatexPreprocessor:
	"""Assemble and clean a paper's LaTeX source for LLM consumption."""

	def __init__(self) -> None:
		self._logger = getLogger(__name__)

	def assemble(self, source_dir: Path, main_tex_file: str | None = None) -> AssembledLatex:
		"""Assemble the document starting from its main ``.tex`` file.

		Args:
		    source_dir: Directory containing the extracted LaTeX source.
		    main_tex_file: Filename of the toplevel ``.tex`` (e.g. from arXiv's
		        ``00README.json``).  When ``None`` it is detected by scanning
		        for ``\\begin{document}``.

		Returns:
		    The assembled body (comments stripped, includes resolved) together
		    with the list of author-defined macro definitions.
		"""
		main_path = self._resolve_main_path(source_dir, main_tex_file)
		if main_path is None:
			self._logger.warning(
				'No main .tex found in %s; falling back to concatenation', source_dir
			)
			return self._fallback_concat(source_dir)

		self._logger.info('Assembling LaTeX from main file %s', main_path.name)
		body = self._expand_includes(main_path, source_dir, visited=set(), depth=0)
		macros = self._extract_macros(body)
		return AssembledLatex(body=body, macros=macros)

	# ------------------------------------------------------------------
	# Main-file detection
	# ------------------------------------------------------------------

	def _resolve_main_path(self, source_dir: Path, main_tex_file: str | None) -> Path | None:
		if main_tex_file:
			candidate = source_dir / main_tex_file
			if candidate.exists():
				return candidate
			# README may give a path relative to a subdir; search by name.
			for match in source_dir.rglob(main_tex_file):
				return match

		# Detect by \documentclass + \begin{document}; prefer files with both.
		best: Path | None = None
		for tex_file in sorted(source_dir.rglob('*.tex')):
			text = self._read(tex_file)
			if '\\begin{document}' not in text:
				continue
			if '\\documentclass' in text:
				return tex_file
			best = best or tex_file
		return best

	# ------------------------------------------------------------------
	# Include resolution
	# ------------------------------------------------------------------

	def _expand_includes(
		self, tex_path: Path, source_dir: Path, visited: set[Path], depth: int
	) -> str:
		resolved = tex_path.resolve()
		if resolved in visited or depth > _MAX_INCLUDE_DEPTH:
			return ''
		visited.add(resolved)

		out: list[str] = []
		for raw_line in self._read(tex_path).splitlines():
			line = _COMMENT_RE.sub('', raw_line)
			match = _INCLUDE_RE.search(line)
			if match is None:
				out.append(line)
				continue

			included = self._resolve_include_target(match.group(1), tex_path, source_dir)
			before = line[: match.start()].rstrip()
			if before:
				out.append(before)
			if included is not None:
				out.append(self._expand_includes(included, source_dir, visited, depth + 1))
			else:
				self._logger.debug('Unresolved include %r in %s', match.group(1), tex_path.name)
		return '\n'.join(out)

	@staticmethod
	def _resolve_include_target(target: str, tex_path: Path, source_dir: Path) -> Path | None:
		target = target.strip()
		names = (target, f'{target}.tex')
		search_roots = (tex_path.parent, source_dir)
		for root in search_roots:
			for name in names:
				candidate = root / name
				if candidate.exists() and candidate.is_file():
					return candidate
		return None

	# ------------------------------------------------------------------
	# Macro extraction
	# ------------------------------------------------------------------

	@staticmethod
	def _extract_macros(body: str) -> list[str]:
		macros: list[str] = []
		seen: set[str] = set()
		for line in body.splitlines():
			if _MACRO_RE.match(line):
				stripped = line.strip()
				if stripped not in seen:
					seen.add(stripped)
					macros.append(stripped)
		return macros

	# ------------------------------------------------------------------
	# Fallbacks / IO
	# ------------------------------------------------------------------

	def _fallback_concat(self, source_dir: Path) -> AssembledLatex:
		parts = [self._read(f) for f in sorted(source_dir.rglob('*.tex'))]
		body = '\n\n'.join(
			'\n'.join(_COMMENT_RE.sub('', line) for line in part.splitlines()) for part in parts
		)
		return AssembledLatex(body=body, macros=self._extract_macros(body))

	def _read(self, path: Path) -> str:
		try:
			return path.read_text(encoding='utf-8', errors='ignore')
		except Exception:
			self._logger.warning('Failed to read %s', path, exc_info=True)
			return ''
