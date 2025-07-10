from domain.repositories import IArxivSourceFetcher
from typing import Final
from domain.entities.arxiv import ArxivPaperAuthor, ArxivPaperId, ArxivPaperMetadata
from domain.entities.compile_setting import CompileSetting
from logging import getLogger
import json
import requests
import tarfile
import yaml
from io import BytesIO
import os
from pathlib import Path
import arxiv
from pydantic import HttpUrl


class ArxivSourceFetcher(IArxivSourceFetcher):
    """
    A repository for fetching the latex source of a paper from arXiv.
    """

    def __init__(self, arxiv_src_url: str = "https://arxiv.org/src"):
        self._arxiv_src_url: Final[str] = arxiv_src_url
        self._logger = getLogger(__name__)
        self._arxiv_client: arxiv.Client = arxiv.Client()

    def fetch_tex_source(
        self, paper_id: ArxivPaperId, output_dir: str
    ) -> CompileSetting:
        self._logger.info("Fetching tex source for paper %s", paper_id)
        # 0. create the output directory if it doesn't exist
        tar_src_url = f"{self._arxiv_src_url}/{paper_id.root}"
        source_dir = Path(os.path.join(output_dir, paper_id.root))
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)
        self._logger.info("Downloading tar source from %s", tar_src_url)
        # 1. Download the paper's source tarfile and extract it to the output directory
        response = requests.get(tar_src_url)
        response.raise_for_status()
        with tarfile.open(fileobj=BytesIO(response.content), mode="r|gz") as tar:
            tar.extractall(path=source_dir)
        # 2. find bibtex file
        bibtex_file_candidates = list(source_dir.rglob("*.bib"))
        # 3. find 00README.json or 00README.yaml in the output directory
        readme_file_candidates = list(source_dir.glob("00README.*"))
        if len(readme_file_candidates) == 0:
            self._logger.warning(
                "No 00README.json or 00README.yaml found in the source directory"
            )
            # この場合は、source_dirの中にあるtexファイルを探して、それをtarget_file_nameとして使う
            tex_file_candidates = list(source_dir.rglob("*.tex"))
            if len(tex_file_candidates) == 0:
                raise FileNotFoundError("No tex file found in the source directory")
            # \begin{document}を含むtexファイルを探す
            for tex_file in tex_file_candidates:
                with open(tex_file, "r") as f:
                    if "\\begin{document}" in f.read():
                        target_file_name = tex_file.name
                        break
            if target_file_name is None:
                raise FileNotFoundError(
                    "No tex file with \\begin{document} found in the source directory"
                )
            self._logger.info("Using %s as the target file name", target_file_name)
            return CompileSetting(
                engine="pdflatex",
                use_bibtex=len(bibtex_file_candidates) > 0,
                target_file_name=target_file_name,
                source_directory=str(source_dir),
            )
        else:
            readme_file = readme_file_candidates[0]
            if readme_file.name.endswith(".json"):
                with open(readme_file, "r") as f:
                    readme_data = json.load(f)
                target_file_name = next(
                    (
                        src["filename"]
                        for src in readme_data["sources"]
                        if src["usage"] == "toplevel"
                    ),
                    None,
                )
                compile_engine = readme_data["process"]["compiler"]
                if target_file_name is None:
                    raise FileNotFoundError(
                        "No toplevel file found in the source directory"
                    )
                return CompileSetting(
                    engine=compile_engine,
                    use_bibtex=len(bibtex_file_candidates) > 0,
                    target_file_name=target_file_name,
                    source_directory=str(source_dir),
                )
            elif readme_file.name.endswith(".yaml"):
                with open(readme_file, "r") as f:
                    readme_data = yaml.safe_load(f)
                compile_engine = readme_data["process"]["compiler"]
                target_file_name = next(
                    (
                        src["filename"]
                        for src in readme_data["sources"]
                        if src["usage"] == "toplevel"
                    ),
                    None,
                )
                if target_file_name is None:
                    raise FileNotFoundError(
                        "No toplevel file found in the source directory"
                    )
                return CompileSetting(
                    engine=compile_engine,
                    use_bibtex=len(bibtex_file_candidates) > 0,
                    target_file_name=target_file_name,
                    source_directory=str(source_dir),
                )
            else:
                raise ValueError("Unknown readme file format")

    def fetch_paper_metadata(self, paper_id: ArxivPaperId) -> ArxivPaperMetadata:
        """
        Fetch the metadata of a paper from arXiv.

        Args:
            paper_id (ArxivPaperId): The ID of the paper to fetch the metadata for.

        Returns:
            ArxivPaperMetadata: The metadata of the paper.
        """
        search = arxiv.Search(
            id_list=[paper_id.root],
        )
        paper = self._arxiv_client.results(search)
        paper_list = list(paper)
        if len(paper_list) == 0:
            raise ValueError(f"Paper {paper_id.root} not found")
        self._logger.info("Found %d papers", len(paper_list))
        paper = paper_list[0]

        return ArxivPaperMetadata(
            paper_id=paper_id,
            title=paper.title,
            summary=paper.summary,
            published_date=paper.published,
            authors=[ArxivPaperAuthor(name=author.name) for author in paper.authors],
            source_url=(
                HttpUrl(paper.pdf_url)
                if paper.pdf_url
                else HttpUrl(paper.links[0].href)
            ),
        )
