# tokubai-mcp — スーパー特売・ポイントデー情報 MCP サーバー

近くのスーパーを登録すると、チェーンごとの**ポイントデー・割引デー・特売**を
カレンダーとして取得し、**最もお得な買い物日**を提案する MCP サーバーです。

AI アシスタント（Claude / 各種 LLM クライアント）が MCP 経由で呼び出すことを想定した
**B2B / API 型プロダクト**です。消費者向けチラシアプリ（トクバイ・Shufoo! 等）が飽和した
レッドオーシャンを避け、「特売情報を AI から使えるツールとして提供する」という
ほぼ無競争の領域を狙います。

## なぜ MCP サーバーなのか（収益化の考え方）

- **収益モデルが明快**: API 従量課金・席課金・B2B ライセンス。献立アプリ、音声アシスタント、
  スマート家電、家計簿アプリなどに「特売・ポイント連携」を提供できる。
- **追い風**: 「AI が今週の特売とポイントデーを把握して最安の買い物日を提案する」は
  MCP / エージェントの流れにそのまま乗る。
- **データの壁を回避**: 日本のスーパーのポイントデーは*規則的*（イオンの 20・30 日
  お客様感謝デー、イトーヨーカドーのハッピーデー 8・18・28 日 等）。これを
  **ルールエンジン**として実装したため、チラシをスクレイプしなくても任意の月の
  カレンダーを動的生成できる。本番ではチラシ配信 API に差し替え可能な
  `DealProvider` ポートで抽象化済み。

## アーキテクチャ

リポジトリ既存サービス（`pdf_analysis` 等）と同じ onion / clean architecture。

```
tokubai_mcp/
├── server.py            MCP エントリ (FastMCP) — ツール定義
├── dependencies.py      DI 配線
├── domain/
│   ├── entities/        GeoPoint / Store / Deal / Calendar (pydantic 値オブジェクト)
│   ├── gateways/        StoreRepository / DealProvider (抽象ポート)
│   └── errors/          ドメインエラー
├── infrastructure/
│   ├── memory/          InMemoryStoreRepository
│   └── sample/          chain_rules（チェーン別ポイントデー規則）/ RuleBasedDealProvider / 店舗カタログ
├── usecase/             register_store / search_stores / build_calendar / find_best_day
└── tests/               pytest
```

データ供給は `DealProvider` ポートで抽象化されており、サンプルの
`RuleBasedDealProvider`（規則ベース）を、実データ連携実装に差し替えられます。

## MCP ツール一覧

| ツール | 説明 |
| --- | --- |
| `list_supported_chains` | ポイントデー規則を持つ対応チェーン一覧 |
| `search_nearby_stores` | 緯度経度から近隣スーパーを距離順に検索 |
| `register_store` | 近くのスーパーを登録 |
| `list_registered_stores` | 登録済み店舗一覧 |
| `unregister_store` | 登録解除 |
| `get_deal_calendar` | 期間の特売カレンダー（特売がある日のみ） |
| `get_point_days` | 指定店舗のポイントデーのみ抽出 |
| `find_best_shopping_day` | 期間内で最もお得な買い物日をランキング |

`find_best_shopping_day` の実効割引率は
`最大割引率(%) + (最大ポイント倍率 − 1) × 基本ポイント率(%)`（既定 1.0%）で概算します。

## ローカル起動

```bash
cd tokubai_mcp
cp .env.template .env

# stdio で起動（MCP クライアントから接続）
uv run python server.py
```

### Claude Desktop / Claude Code への登録例

```json
{
  "mcpServers": {
    "tokubai": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/absolute/path/to/jaXiv/tokubai_mcp"
    }
  }
}
```

## 開発

```bash
uv run pytest        # テスト
uv run ruff check .  # lint
uv run ruff format . # format
uv run mypy .        # 型チェック
```

## サンプルデータについて

`infrastructure/sample/` のチェーン規則・店舗カタログは、実在チェーンの
代表的な定期施策を**規則として再現したイラストレーション用データ**です。
正確な最新情報は各社公式をご確認ください。本番運用ではチラシ配信 API 等の
実データソースを `DealProvider` 実装として接続してください。
