# Use the pre-built base image with Python + TeX Live Full
ARG BASE_IMAGE_URL
FROM ${BASE_IMAGE_URL:-python:3.13-slim}

# Set the working directory (in case base image doesn't have it)
WORKDIR /app

# Dependency management
COPY pyproject.toml uv.lock ./
RUN uv sync

# Application code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
