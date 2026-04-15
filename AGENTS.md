# AGENTS.md

## Cursor Cloud specific instructions

### Architecture overview

jaXiv is a multi-service application for translating arXiv papers (English → Japanese) and generating blog posts from academic PDFs. It consists of:

| Service | Tech | Port | Directory |
|---------|------|------|-----------|
| Backend API | FastAPI (Python 3.13, uv) | 8000 | `backend/` |
| PDF Analysis | FastAPI (Python 3.13, uv) | 7860 | `pdf_analysis/` |
| Frontend | React Router + Cloudflare Workers (Node, npm) | 5173 | `frontend/` |
| PostgreSQL | Docker (postgres:16-alpine) | 5434 (host) | via `docker-compose.yml` |
| Qdrant | Docker (qdrant/qdrant) | 6333 | via `docker-compose.yml` |

### Starting infrastructure services

```bash
# Start PostgreSQL and Qdrant (required by backend)
docker compose up -d db qdrant

# Run DB migrations (from backend/)
cd backend && uv run alembic upgrade head
```

### Starting application services

```bash
# Backend API (from backend/)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# PDF Analysis (from pdf_analysis/)
uv run uvicorn main:app --host 0.0.0.0 --port 7860 --reload

# Frontend dev server (from frontend/) — requires CLOUDFLARE_API_TOKEN (see note below)
npm run dev
```

### Backend .env file

The backend requires a `.env` file at `backend/.env`. Key variables:

- `POSTGRES_URL` — set to `postgresql://jaxiv:jaxiv@localhost:5434/jaxiv` for local Docker
- `QDRANT_URL` — set to `http://localhost:6333`
- `LAYOUT_ANALYSIS_URL` — set to `http://localhost:7860`
- `SUPABASE_URL`, `SUPABASE_KEY`, `BUCKET_NAME`, `BLOG_FIGURES_BUCKET_NAME` — Supabase storage (required for PDF/blog storage features)
- `MISTRAL_API_KEY` — Mistral AI API key (required for translation)
- `GEMINI_API_KEY` — Google Gemini API key (required for blog generation)
- `QDRANT_API_KEY` — Qdrant API key

### Lint and type check commands

See `frontend/package.json` scripts and `backend/pyproject.toml` / `pdf_analysis/pyproject.toml` dev dependencies. Key commands:

- **Frontend**: `npm run lint` (ESLint), `npm run typecheck` (react-router typegen + tsc)
- **Backend**: `uv run ruff check .`, `uv run mypy .`
- **PDF Analysis**: `uv run ruff check .`, `uv run mypy .` (has pre-existing mypy errors from `transformers` stubs)

### Important caveats

- **Frontend dev server requires Cloudflare authentication**: `npm run dev` uses the `@cloudflare/vite-plugin` which requires a valid `CLOUDFLARE_API_TOKEN` env var (or `wrangler login`) because the Workers AI binding (`ai.binding` in `wrangler.jsonc`) always connects remotely. Without it, the dev server times out. The frontend **builds** correctly without credentials (`npm run build`).
- **React Router typegen**: Before running `npx tsc --noEmit`, you must first run `npx react-router typegen` to generate route types (`app/+types/`). The `npm run typecheck` script does both.
- **pdf_analysis mypy**: Has 6 pre-existing false positive errors from `transformers` library stubs (`AutoTokenizer`, `AutoModel`, `AutoImageProcessor` not callable). These are expected and not regressions.
- **Qdrant API key warning**: When using a placeholder `QDRANT_API_KEY` with local Qdrant (non-TLS), you'll see a `UserWarning: Api key is used with an insecure connection` warning. This is harmless in local dev.
- **DDD architecture**: The codebase follows Domain-Driven Design with Onion/Clean Architecture. See `.cursor/rules/implementation.mdc` for detailed conventions.
