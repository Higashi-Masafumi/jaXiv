"""Download ML model weights required at runtime.

Run this script once before starting the application:
    uv run python scripts/download_models.py
"""

from huggingface_hub import hf_hub_download, snapshot_download

DOCLAYOUT_YOLO_REPO = "wybxc/DocLayout-YOLO-DocStructBench-onnx"
DOCLAYOUT_YOLO_FILE = "doclayout_yolo_docstructbench_imgsz1024.onnx"
FIGURE_EMBEDDING_MODEL_REPO = "llamaindex/vdr-2b-multi-v1"
TEXT_EMBEDDING_MODEL_REPO = "BAAI/bge-base-en-v1.5"


def download_doclayout_yolo() -> str:
    path = hf_hub_download(repo_id=DOCLAYOUT_YOLO_REPO, filename=DOCLAYOUT_YOLO_FILE)
    print(f"DocLayout-YOLO model ready: {path}")
    return path


def download_figure_embedding_model() -> str:
    path = snapshot_download(repo_id=FIGURE_EMBEDDING_MODEL_REPO)
    print(f"Figure embedding model ready: {path}")
    return path


def download_text_embedding_model() -> str:
    path = snapshot_download(repo_id=TEXT_EMBEDDING_MODEL_REPO)
    print(f"Text embedding model ready: {path}")
    return path


def main() -> None:
    download_doclayout_yolo()
    download_figure_embedding_model()
    download_text_embedding_model()


if __name__ == "__main__":
    main()
