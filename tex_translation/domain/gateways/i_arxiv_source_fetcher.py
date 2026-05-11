from abc import ABC, abstractmethod

from domain.value_objects import ArxivPaperId, CompileSetting


class IArxivSourceFetcher(ABC):
    """Gateway for fetching the LaTeX source archive from arXiv."""

    @abstractmethod
    def fetch_tex_source(
        self, paper_id: ArxivPaperId, output_dir: str
    ) -> CompileSetting:
        """Download the LaTeX source for ``paper_id`` and resolve the compile setting.

        Raises:
            TexFileNotFoundError: When no ``.tex`` file with ``\\begin{document}`` is found.
            ArxivPaperNotFoundError: When the paper cannot be retrieved.
        """
