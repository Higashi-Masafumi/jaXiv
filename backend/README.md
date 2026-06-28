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

MinIO / Qdrant / PDF 解析サービスはリポジトリルートの `docker compose up`、Postgres は Supabase CLI で起動します（詳細は[ルート README](../README.md) 参照）。

## オブジェクトストレージ（翻訳 PDF・図表）

翻訳済み PDF とブログ図表は S3 互換のオブジェクトストレージへ保存し、公開 URL で配信します。実装は `infrastructure/s3/` にあり、`IFileStorageRepository` / `IFigureStorageRepository` を満たします。エンドポイントと認証情報を差し替えるだけで **Cloudflare R2 / AWS S3 / Backblaze B2 / MinIO** など任意の S3 互換プロバイダを利用できます。

本番環境では、公開アセットの配信（下り）が支配的な用途のため **Cloudflare R2** を使用します。バケットは「公開バケット」としてカスタムドメインに紐付け、その配信元 URL を `*_PUBLIC_BASE_URL` に設定します。ローカル開発では S3 互換の MinIO を使用します。

| 環境変数 | 必須 | 説明 |
| --- | --- | --- |
| `S3_ENDPOINT_URL` | ✅ | S3 互換エンドポイント。R2 は `https://<account_id>.r2.cloudflarestorage.com`、ローカル MinIO は `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | ✅ | アクセスキー ID（シークレット） |
| `S3_SECRET_ACCESS_KEY` | ✅ | シークレットアクセスキー（シークレット） |
| `S3_REGION` | - | リージョン。R2 は `auto`、ローカル MinIO は `us-east-1` |
| `TRANSLATED_ARXIV_BUCKET_NAME` | - | 翻訳 PDF 用バケット名（既定 `translated-arxiv-bucket`） |
| `BLOG_FIGURES_BUCKET_NAME` | - | 図表用バケット名（既定 `blog-figures`） |
| `TRANSLATED_ARXIV_PUBLIC_BASE_URL` | ✅ | 翻訳 PDF バケットの公開配信元 URL（例: `https://pdf.example.com`） |
| `BLOG_FIGURES_PUBLIC_BASE_URL` | ✅ | 図表バケットの公開配信元 URL（例: `https://figures.example.com`） |

### Cloudflare R2 本番構成

| 用途 | バケット | 公開ドメイン |
| --- | --- | --- |
| 翻訳 PDF | `translated-arxiv-bucket` | `https://pdf.jaxiv.utstudent-scienceblog.com` |
| ブログ図表 | `blog-figures` | `https://figures.jaxiv.utstudent-scienceblog.com` |

両バケットは APAC / Standard で作成し、カスタムドメインの最小 TLS バージョンは 1.2 に設定します。`r2.dev` の公開URLは無効化し、CORS は本番フロントエンド、Workers デフォルトURL、ローカル開発元からの `GET` / `HEAD` のみ許可します。

本番用の S3 認証情報は Cloudflare R2 で Object Read & Write 権限のAPIトークンを作成し、上記2バケットのみにスコープします。Access Key ID と Secret Access Key は `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` として本番環境のシークレットに設定し、リポジトリへはコミットしません。

> 既存ファイルの移行は別途。本変更は**新規書き込みのみ** S3 互換ストレージへ切り替えるものです（過去に Supabase Storage に保存済みの URL はそのまま有効）。

### ローカル開発構成

Cloudflare のローカル R2 は Wrangler / Miniflare の Workers binding として提供され、S3 API endpoint としては公開されません。このバックエンドは boto3 の S3 API を利用するため、ローカルでは MinIO を R2 の代替として使用します。

ルートで `docker compose up --build --watch` を実行すると、MinIO と次の公開バケットが自動で作成されます。

| 用途 | バケット | 公開 URL |
| --- | --- | --- |
| 翻訳 PDF | `translated-arxiv-bucket` | `http://localhost:9000/translated-arxiv-bucket` |
| ブログ図表 | `blog-figures` | `http://localhost:9000/blog-figures` |

MinIO Console は `http://localhost:9001` で、ローカルのユーザー名・パスワードはともに `minioadmin` です。データは `minio-data` Docker volume に保持され、`docker compose down -v` で削除されます。

MinIO は R2 固有機能まで再現する完全なエミュレーターではありません。現在のバックエンドが使う基本的な S3 オブジェクト書き込みと公開読み取りはローカルで確認できますが、R2 の CORS、カスタムドメイン、ライフサイクルなどは Cloudflare 側の環境で確認してください。

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
