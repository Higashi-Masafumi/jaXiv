FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

# 実行時は compose の HF_HOME=/app/.cache/hf と揃える（未設定だと ~/.cache/huggingface になりパスがずれる）
# HF の重いモデルはビルドで取得しない。compose で ./pdf_analysis/.cache をマウントするためイメージに焼いても無駄になりやすく、ビルド失敗の原因にもなる
ENV HF_HOME=/app/.cache/hf

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY . .

EXPOSE 7860
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
