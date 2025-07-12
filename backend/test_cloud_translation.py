from infrastructure.google.cloud_latex_translator import CloudLatexTranslator
from infrastructure.arxiv_source_fetcher import ArxivSourceFetcher
from domain.entities import ArxivPaperId, TargetLanguage, LatexFile
from utils.preprocess import replace_escaped_latex_commands_with_html_entities
from utils.postprocess import replace_html_entities_with_latex_commands
import pytest
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio
load_dotenv()

@pytest.fixture
def arxiv_paper_id() -> ArxivPaperId:
    return ArxivPaperId(root="2112.10752")


@pytest.fixture
def arxiv_source_fetcher() -> ArxivSourceFetcher:
    return ArxivSourceFetcher()


@pytest.fixture
def output_dir() -> str:
    return "translated_output"


@pytest.fixture
def get_google_project_id() -> str:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if project_id is None:
        raise ValueError("GOOGLE_CLOUD_PROJECT_ID is not set")
    return project_id


@pytest.fixture
def cloud_latex_translator(get_google_project_id: str) -> CloudLatexTranslator:
    return CloudLatexTranslator(project_id=get_google_project_id)


def test_translate_latex(
    arxiv_paper_id: ArxivPaperId,
    arxiv_source_fetcher: ArxivSourceFetcher,
    output_dir: str,
    cloud_latex_translator: CloudLatexTranslator,
):
    compile_setting = arxiv_source_fetcher.fetch_tex_source(arxiv_paper_id, output_dir)
    print(compile_setting)
    tex_files = Path(output_dir).rglob("*.tex")
    for tex_file in tex_files:
        with open(tex_file, "r") as f:
            tex_content = f.read()
        tex_content = replace_escaped_latex_commands_with_html_entities(tex_content)
        latex_file = LatexFile(
            path=str(tex_file),
            content=tex_content,
        )
        translated_latex_file = asyncio.run(
            cloud_latex_translator.translate(latex_file, TargetLanguage.JAPANESE)
        )
        translated_latex_file.content = replace_html_entities_with_latex_commands(
            translated_latex_file.content
        )
        with open(translated_latex_file.path, "w") as f:
            f.write(translated_latex_file.content)

