from infrastructure.arxiv_source_fetcher import ArxivSourceFetcher
from infrastructure.google.cloud_latex_translator import CloudLatexTranslator
from domain.entities import ArxivPaperId
import pytest

@pytest.fixture
def arxiv_paper_id() -> ArxivPaperId:
    return ArxivPaperId(root="2112.10752")


@pytest.fixture
def arxiv_source_fetcher() -> ArxivSourceFetcher:
    return ArxivSourceFetcher()


@pytest.fixture
def output_dir() -> str:
    return "raw_output"


def test_fetch_tex_source(
    arxiv_paper_id: ArxivPaperId,
    arxiv_source_fetcher: ArxivSourceFetcher,
    output_dir: str,
):
    compile_setting = arxiv_source_fetcher.fetch_tex_source(arxiv_paper_id, output_dir)
    print(compile_setting)