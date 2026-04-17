# jaXiv Backend

arXiv ID を受け取り、ソースをダウンロードして翻訳・TeX 再コンパイルを行う FastAPI サーバー。

## 構成

- FastAPI + SQLModel / SQLAlchemy (async)
- Postgres（Alembic でマイグレーション管理）
- Qdrant（ベクトル検索）
- TeX コンパイル（`texlive-full` 依存）
- PDF レイアウト解析サービス（`pdf_analysis/`）と連携

ディレクトリは `domain / application / infrastructure / controller` の層構成。

## セットアップ

```bash
pip install uv
uv sync
```

環境変数は `.env` に記載します（`docker-compose.yml` の `env_file` 参照）。

Postgres / Qdrant / PDF 解析サービスはリポジトリルートの `docker compose up` で起動するのが簡単です（詳細は[ルート README](../README.md) 参照）。

## `just` レシピ

`.justfile` に開発用タスクを定義しています。[`just`](https://github.com/casey/just) をインストール後、`backend/` ディレクトリで以下のコマンドが使えます。

| コマンド | 内容 |
| --- | --- |
| `just start` | `uvicorn main:app --host 0.0.0.0 --port 8001 --reload` で起動 |
| `just format` | `ruff check --fix` と `ruff format` を実行 |
| `just lint` | `ruff check` と `mypy` を実行 |
| `just migrate` | `alembic upgrade head` |
| `just rollback` | `alembic downgrade -1` |
| `just gen-migration <name>` | `alembic revision --autogenerate -m "<name>"` でマイグレーションを生成 |
| `just gen-oapi` | `scripts.generate_openapi` を実行して `openapi.json` を更新 |

`just` のインストール例:

```bash
# macOS
brew install just
# cargo
cargo install just
```

## Docker イメージ

`texlive-full` のインストールに時間がかかるため、ベースイメージを分離しています。

1. ベースイメージ (`texlive-full` + `uv`) をビルド:

    ```bash
    docker build -f backend/Dockerfile.base -t backend-base:local backend
    ```

2. アプリイメージをビルド:

    ```bash
    docker build \
        -f backend/Dockerfile \
        --build-arg BASE_IMAGE_URL=backend-base:local \
        -t jaxiv-backend:dev \
        backend
    ```

3. 起動:

    ```bash
    docker run --rm -it -p 8000:8000 jaxiv-backend:dev
    ```

## OpenAPI

`just gen-oapi` で生成される `openapi.json` は、フロントエンドの型生成 (`openapi-ts`) に利用されます。
