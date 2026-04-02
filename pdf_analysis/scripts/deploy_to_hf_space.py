"""Deploy pdf_analysis service to Hugging Face Spaces.

Requires HUGGINGFACE_TOKEN and HF_SPACE_REPO_ID environment variables.

Usage:
    HUGGINGFACE_TOKEN=hf_xxx HF_SPACE_REPO_ID=user/space-name \
        uv run python scripts/deploy_to_hf_space.py
"""

import os
from pathlib import Path
from logging import getLogger

from huggingface_hub import HfApi

TOKEN = os.environ["HUGGINGFACE_TOKEN"]
FOLDER = Path(__file__).resolve().parent.parent
logger = getLogger(__name__)


def main() -> None:
    api = HfApi(token=TOKEN)

    api.create_repo(
        repo_id="masamasa4/jaxiv-pdf-analysis",
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
    )

    api.upload_folder(
        folder_path=str(FOLDER),
        repo_id="masamasa4/jaxiv-pdf-analysis",
        repo_type="space",
        commit_message="Deploy pdf_analysis from monorepo",
        ignore_patterns=["scripts/deploy_to_hf_space.py", ".venv/", "__pycache__/"],
    )

    logger.info("Deployed to https://huggingface.co/spaces/masamasa4/jaxiv-pdf-analysis")


if __name__ == "__main__":
    main()
