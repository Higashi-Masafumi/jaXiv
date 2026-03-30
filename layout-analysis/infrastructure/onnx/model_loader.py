from huggingface_hub import hf_hub_download
from onnxruntime import InferenceSession

REPO_ID = "wybxc/DocLayout-YOLO-DocStructBench-onnx"
MODEL_FILE = "doclayout_yolo_docstructbench_imgsz1024.onnx"


def load_onnx_session() -> InferenceSession:
    model_path = hf_hub_download(repo_id=REPO_ID, filename=MODEL_FILE)
    return InferenceSession(model_path, providers=["CPUExecutionProvider"])
