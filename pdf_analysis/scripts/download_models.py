"""Download ML model weights required at runtime.

Run this script once before starting the application:
    uv run python scripts/download_models.py
"""

from huggingface_hub import hf_hub_download, snapshot_download

DOCLAYOUT_YOLO_REPO = "wybxc/DocLayout-YOLO-DocStructBench-onnx"
DOCLAYOUT_YOLO_FILE = "doclayout_yolo_docstructbench_imgsz1024.onnx"
EMBEDDING_MODEL_REPO = "llamaindex/vdr-2b-multi-v1"


def download_doclayout_yolo() -> str:
    path = hf_hub_download(repo_id=DOCLAYOUT_YOLO_REPO, filename=DOCLAYOUT_YOLO_FILE)
    print(f"DocLayout-YOLO model ready: {path}")
    return path


def download_embedding_model() -> str:
    path = snapshot_download(repo_id=EMBEDDING_MODEL_REPO)
    print(f"Embedding model ready: {path}")
    return path


def main() -> None:
    download_doclayout_yolo()
    download_embedding_model()


if __name__ == "__main__":
    main()
