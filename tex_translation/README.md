# tex_translation

ArXivのTeX原稿を取得し、LLMで翻訳して、TeX Liveでコンパイルする独立マイクロサービス。
バックエンドからHTTPで呼び出されるRender private serviceとしての利用を想定している。

## 構成

DDD / Onion architecture (`pdf_analysis`サービスと同じスタイル)。

```
tex_translation/
├── controller/        FastAPI 入口層
├── domain/            純粋ドメイン (entities/errors/gateways/services/value_objects)
├── infrastructure/    外部I/O (arxiv API / Mistral / latex subprocess)
├── usecase/           ユースケース
├── dependencies.py    DI ルート
└── main.py            FastAPI app
```

## API

- `POST /api/v1/translate/{arxiv_paper_id}?target_language=japanese`
  - arXivから`.tar.gz`ソースを取得 → 各`.tex`をMistralで翻訳 → `latexmk`でPDF化
  - 成功時: `application/pdf` をbinaryで返却
  - 失敗時: 4xx / 5xx + JSON エラー

- `GET /health` ヘルスチェック

## 必要な環境変数

- `MISTRAL_API_KEY` Mistral APIキー (Codestral)

## 開発

```
docker compose up --watch
```

`docker-compose.yml` から `tex-translation` サービスとして起動される (port 8100)。
