gen-oapi:
    uv run python -m scripts.generate_openapi

# Compare figure search modes (caption/image/hybrid) on a labelled query set.
# Provide your own scripts/figure_search_eval.json (see *.example.json).
eval-figures dataset="scripts/figure_search_eval.json":
    uv run python -m scripts.eval_figure_search --dataset {{dataset}}
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
