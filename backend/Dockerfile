FROM python:3.13-slim

# Install LaTeX environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-full \
    latexmk ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Install Python package manager
RUN pip install uv

# Set the working directory
WORKDIR /app

# Dependency management
COPY pyproject.toml uv.lock ./
RUN uv sync

# Application code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
