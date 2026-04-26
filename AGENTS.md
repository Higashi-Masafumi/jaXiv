# jaxiv開発手順

## サービス構成

```
├── backend     バックエンドサービス（翻訳機能、チャット機能）
├── frontend    フロントエンドサービス（認証、ブログ管理）
├── pdf_analysis    pdf分析用の分離サービス（チャンキング、レイアウト分析）
├── README.md
├── render.yaml バックエンドをrenderにデプロイする設定
├── supabase    データベース
└── terraform   インフラ管理（今は利用していない）
```

## 開発セットアップ
1. DBのセットアップ
```
$ supabase start
```

2. バックエンドの立ち上げ
```
$ docker compose up --watch
```

3. フロンエンドの立ち上げ
```
$ cd frontend
$ npm run dev
```

## 自動生成ファイルの管理

自動生成で管理されているファイルは手動で作ることなく必ず自動生成のコマンドを実行してください

- マイグレーションの生成
    sqlalchemyのautogerateを使っている。以下のコマンドで生成する
    ```
    $ cd backend
    $ just gen-migration "xxxxx"
    ```

- openapiの生成
    openapi生成用のスクリプトを`/backend/scripts/generate_openapi.py`に用意している
    ```
    $ cd backend
    $ just gen-oapi
    ```

- フロントエンドのopenapiクライアントの生成
    hey-openapiで型とクライアントを自動生成している
    ```
    $ cd frontend
    $ npm run generate-api
    ```

## コーディング規約

- pythonにおいては型安全性を重視して、`pydantic`を利用する
- プライベートメソッドは基本的に最低限に抑え、再定義不要な関数はインラインで実装する
- typescriptにおける`as`など型推論を無駄にするコードは書かない
- hey-openapiなどできるだけ自動生成の実装を利用するようにして、バックエンドとフロントエンドの整合性を保つようにして保守性を上げること