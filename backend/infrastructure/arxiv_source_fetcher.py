import re
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
            compile_setting = CompileSetting(
                engine="pdflatex",
                use_bibtex=len(bibtex_file_candidates) > 0,
                target_file_name=target_file_name,
                source_directory=str(source_dir),
            )
            return self._merge_tex_files(compile_setting)
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
                compile_setting = CompileSetting(
                    engine=compile_engine,
                    use_bibtex=len(bibtex_file_candidates) > 0,
                    target_file_name=target_file_name,
                    source_directory=str(source_dir),
                )
            else:
                raise ValueError("Unknown readme file format")
            return self._merge_tex_files(compile_setting)

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

    def _merge_tex_files(self, compile_setting: CompileSetting) -> CompileSetting:
        """
        Merge tex files by replacing \\input{} commands with actual file contents.

        Args:
            compile_setting: The compile setting containing source directory and target file info

        Returns:
            CompileSetting: Updated compile setting after merging
        """
        source_dir = Path(compile_setting.source_directory)
        target_file_path = source_dir / compile_setting.target_file_name

        if not target_file_path.exists():
            self._logger.warning(f"Target file {target_file_path} does not exist")
            return compile_setting

        # Keep track of already processed files to avoid infinite loops
        processed_files = set()
        files_to_delete = set()

        def expand_inputs(file_path: Path) -> str:
            """Recursively expand \\input{} commands in a tex file."""
            if file_path in processed_files:
                self._logger.warning(f"Circular reference detected for {file_path}")
                return f"% Circular reference: {file_path.name}\n"

            processed_files.add(file_path)

            if not file_path.exists():
                self._logger.warning(f"File {file_path} does not exist")
                return f"% Missing file: {file_path.name}\n"

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception as e:
                    self._logger.error(f"Failed to read file {file_path}: {e}")
                    return f"% Error reading file: {file_path.name}\n"

            # Find all \input{} commands
            # Pattern matches \input{filename} with optional whitespace
            input_pattern = r"\\input\s*\{\s*([^}]+)\s*\}"

            def replace_input(match):
                input_filename = match.group(1).strip()

                # Add .tex extension if not present
                if not input_filename.endswith(".tex"):
                    input_filename += ".tex"

                input_file_path = source_dir / input_filename

                if input_file_path.exists() and input_file_path != file_path:
                    self._logger.info(f"Expanding input: {input_filename}")
                    # Mark file for deletion after processing
                    files_to_delete.add(input_file_path)
                    # Recursively expand the input file
                    expanded_content = expand_inputs(input_file_path)
                    return f"% Begin content from {input_filename}\n{expanded_content}% End content from {input_filename}\n"
                else:
                    self._logger.warning(
                        f"Input file not found or is the same as current file: {input_filename}"
                    )
                    return f"% Input file not found: {input_filename}\n"

            # Replace all \input{} commands
            expanded_content = re.sub(input_pattern, replace_input, content)

            processed_files.remove(file_path)
            return expanded_content

        try:
            # Expand all inputs in the target file
            self._logger.info(f"Starting to merge tex files for {target_file_path}")
            merged_content = expand_inputs(target_file_path)

            # Write the merged content back to the target file
            with open(target_file_path, "w", encoding="utf-8") as f:
                f.write(merged_content)

            # Delete the files that were merged
            for file_to_delete in files_to_delete:
                try:
                    file_to_delete.unlink()
                    self._logger.info(f"Deleted merged file: {file_to_delete}")
                except Exception as e:
                    self._logger.warning(f"Failed to delete file {file_to_delete}: {e}")

            self._logger.info(
                f"Successfully merged {len(files_to_delete)} files into {target_file_path}"
            )

        except Exception as e:
            self._logger.error(f"Error during tex file merging: {e}")
            # Return original compile setting if merging fails
            return compile_setting

        return compile_setting
