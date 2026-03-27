from abc import ABC, abstractmethod

from domain.entities.arxiv import ArxivPaperMetadata
from domain.value_objects import ArxivPaperId, CompileSetting


class IArxivSourceFetcher(ABC):
	"""Gateway for fetching LaTeX source and metadata from arXiv."""

	@abstractmethod
	def fetch_tex_source(self, paper_id: ArxivPaperId, output_dir: str) -> CompileSetting:
		"""
		Fetch the LaTeX source of a paper from arXiv.

		Args:
		    paper_id: The ID of the paper to fetch.
		    output_dir: The directory to save the source to.

		Returns:
		    CompileSetting for the fetched source.

		Raises:
		    TexFileNotFoundError: If no tex file is found.
		    ArxivPaperNotFoundError: If the paper cannot be found.
		"""
		...

	@abstractmethod
	def fetch_paper_metadata(self, paper_id: ArxivPaperId) -> ArxivPaperMetadata:
		"""
		Fetch the metadata of a paper from arXiv.

		Args:
		    paper_id: The ID of the paper.

		Returns:
		    ArxivPaperMetadata for the paper.

		Raises:
		    ArxivPaperNotFoundError: If the paper cannot be found.
		"""
		...
