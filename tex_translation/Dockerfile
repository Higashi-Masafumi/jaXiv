FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        texlive-full \
        latexmk ghostscript poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync

COPY . .

EXPOSE 8100

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
