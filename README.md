# jaXiv

arXiv 論文をダウンロードして日本語に翻訳・再コンパイルする Web アプリケーション。

## 構成

- `backend/` — FastAPI（翻訳・TeX コンパイル）
- `frontend/` — React Router v7
- `pdf_analysis/` — PDF レイアウト解析サービス
- `supabase/` — Supabase ローカルエミュレータ設定（DB / Auth / Storage）
- `terraform/` — インフラ構成

## 前提ツール

- Docker Desktop
- [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started) (`brew install supabase/tap/supabase`)
- Node.js 20+

## ローカル起動

Supabase CLI（DB / Auth / Storage）、docker compose（API / PDF 解析 / Qdrant）、フロントエンドを別々に起動します。

```bash
# 1. Supabase ローカルエミュレータ
supabase start
supabase seed buckets --local   # 初回のみ: バケット作成

# 2. アプリケーション（API / PDF 解析 / Qdrant）
docker compose up --build --watch

# 3. フロントエンド
cd frontend && npm install && npm run dev
```

公開されるエンドポイント:

| サービス | URL |
| --- | --- |
| フロントエンド | http://localhost:5173 |
| API | http://localhost:8001 |
| PDF 解析 | http://localhost:7860 |
| Qdrant | http://localhost:6333 |
| Supabase Studio | http://127.0.0.1:54323 |
| Supabase Postgres | `postgresql://postgres:postgres@127.0.0.1:54322/postgres` |

鍵類は `supabase status` で確認できます。

## 環境変数

- `supabase/.env.local`（gitignore 済み）に Google OAuth クレデンシャルを置きます:

  ```dotenv
  SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
  SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET=GOCSPX-xxxxxxxxxxxx
  ```

- `backend/.env` には API キー等の **機密値のみ** を置きます。URL 系（`POSTGRES_URL` / `SUPABASE_URL` / `JWKS_URL` 等）は `docker-compose.yml` で固定済みです。
- Google OAuth を使う場合、Google Cloud Console の OAuth クライアントに以下を登録してください:
  - 承認済みリダイレクト URI: `http://127.0.0.1:54321/auth/v1/callback`
  - 承認済み JavaScript 生成元: `http://localhost:5173`

## よく使う Supabase コマンド

| 目的 | コマンド |
| --- | --- |
| 起動 / 停止 | `supabase start` / `supabase stop` |
| `config.toml` の反映 | `supabase stop && supabase start` |
| Storage バケット定義の反映 | `supabase seed buckets --local` |
| DB を完全初期化 | `supabase stop --no-backup && supabase start` |

スキーマ変更は **Alembic**（`backend/alembic/versions/`）で管理し、`docker compose up` 時に `alembic upgrade head` が自動実行されます。

## ホットリロード

`docker-compose.yml` の `develop.watch` により、`backend/` / `pdf_analysis/` 配下のファイル変更は自動で同期・リロードされます。依存関係を完全リセットしたい場合は `docker compose down -v` でボリュームごと削除してください。

## 個別サービスの詳細

- [`backend/README.md`](backend/README.md) — FastAPI / `just` レシピ
- [`frontend/README.md`](frontend/README.md) — React Router v7
