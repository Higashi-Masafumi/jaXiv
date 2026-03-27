gen-oapi:
    uv run python -m scripts.generate_openapi
start:
    uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload

format:
    uv run ruff check . --fix
    uv run ruff format .

lint:
    uv run ruff check .
    uv run mypy .

migrate:
    uv run alembic upgrade head

rollback:
    uv run alembic downgrade -1

gen-migration name:
    uv run alembic revision --autogenerate -m "{{name}}"
