FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY scripts/download_models.py scripts/download_models.py
RUN uv run python scripts/download_models.py

COPY . .

EXPOSE 7860
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
