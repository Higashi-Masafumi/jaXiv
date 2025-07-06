from abc import ABC, abstractmethod
from domain.entities.arxiv import ArxivPaperId
from domain.entities.compile_setting import CompileSetting


class IArxivSourceFetcher(ABC):
    """
    A repository for fetching the latex source of a paper from arXiv.
    """

    @abstractmethod
    def fetch_tex_source(
        self, paper_id: ArxivPaperId, output_dir: str
    ) -> CompileSetting:
        """
        Fetch the latex source of a paper from arXiv.

        Args:
            paper_id (ArxivPaperId): The ID of the paper to fetch the source for.
            output_dir (str): The directory to save the source to.

        Returns:
            CompileSetting: The compile setting.
        """
        pass
