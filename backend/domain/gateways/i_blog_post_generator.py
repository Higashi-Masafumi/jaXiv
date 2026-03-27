from abc import ABC, abstractmethod
from pathlib import Path

from domain.entities.arxiv import ArxivPaperMetadata


class IBlogPostGenerator(ABC):
	"""Gateway for generating blog posts from arXiv papers using an LLM."""

	@abstractmethod
	async def generate(
		self,
		paper_metadata: ArxivPaperMetadata,
		latex_source_dir: Path,
		figure_urls: dict[str, str],
	) -> str:
		"""
		Generate a Markdown blog post from a paper's LaTeX source.

		Args:
		    paper_metadata: The paper's metadata (title, authors, summary, etc.).
		    latex_source_dir: Path to the extracted LaTeX source directory.
		    figure_urls: Mapping of figure filename to its public Supabase Storage URL.

		Returns:
		    The generated blog post content in Markdown.
		"""
		...
