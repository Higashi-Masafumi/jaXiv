FROM python:3.13-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync

COPY . .

# MCP は既定で stdio。HTTP で配信する場合は CMD を
# ["uv","run","python","-m","mcp","run","server.py","--transport","streamable-http"] などに変更する。
CMD ["uv", "run", "python", "server.py"]
