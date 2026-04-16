# jaXiv

arXiv 論文をダウンロードして日本語に翻訳・再コンパイルする Web アプリケーション。

## 構成

- `backend/` — FastAPI による API サーバー（翻訳・TeX コンパイル）
- `frontend/` — React Router v7 製のフロントエンド
- `pdf_analysis/` — PDF レイアウト解析サービス
- `terraform/` — インフラ構成
- `docker-compose.yml` — ローカル開発用の統合環境（Postgres / Qdrant / API / レイアウト解析）

## ローカル起動

初回は `--build` でイメージをビルドします:

```bash
docker compose up --build
```

公開されるエンドポイント:

- API: http://localhost:8001
- PDF 解析: http://localhost:7860
- Postgres: localhost:5434
- Qdrant: http://localhost:6333

## ホットリロード: `docker compose up --watch`

`docker-compose.yml` の各サービスには `develop.watch` が定義してあり、ホスト側のファイル変更をコンテナに自動反映できます。

```bash
docker compose up --watch
```

挙動:

- **ソースコードの変更** (`backend/` `pdf_analysis/` 配下の `.py` など)
  - コンテナ内にファイルが即時同期 (`sync`)
  - `uvicorn --reload` が検知して自動リロード
- **`pyproject.toml` / `uv.lock` の変更**
  - ファイル同期後にコンテナを再起動 (`sync+restart`)
  - 起動コマンドの `uv sync` が走って依存関係が更新される
- **同期対象外**: `.venv/` `__pycache__/` `.git/` `.pytest_cache/` `output/` `.cache/` など

補足:

- `.venv` は名前付きボリューム (`api-venv` / `pdf-analysis-venv`) に永続化されているため、依存関係を完全にリセットしたい場合は `docker compose down -v` でボリュームごと削除してください。
- 環境変数は `backend/.env` を `env_file` で注入しています。`.env` の変更を反映するには対象サービスを再起動 (`docker compose restart api`) する必要があります。
- `--build` と `--watch` は併用可能です: `docker compose up --build --watch`

## 個別サービスの詳細

- [`backend/README.md`](backend/README.md) — FastAPI / `just` レシピ
- [`frontend/README.md`](frontend/README.md) — React Router v7
