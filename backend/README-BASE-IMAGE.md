# バックエンドベースイメージの管理

## 概要

バックエンドのビルド時間を短縮するために、Python + TeX Live Full が含まれたベースイメージを事前に作成して使用します。

## ファイル構成

- `Dockerfile.base`: ベースイメージ用の Dockerfile（Python + TeX Live Full）
- `Dockerfile`: アプリケーション用の Dockerfile（ベースイメージを使用）
- `../cloudbuild-base.yaml`: ベースイメージビルド用の Cloud Build 設定

## 使用手順

### 1. 初回セットアップ（ベースイメージ作成）

```bash
# Terraformでインフラをデプロイ
cd terraform
terraform apply

# GCP Console でベースイメージビルドを手動実行
# Google Cloud Console > Cloud Build > トリガー > "manual-build-backend-base-image" > 実行
```

### 2. ベースイメージの更新が必要な場合

以下の場合にベースイメージを再ビルドする必要があります：

- Python バージョンを変更した場合
- TeX Live のパッケージを追加/変更した場合
- システムパッケージを追加した場合

更新方法：

1. `Dockerfile.base`を編集
2. GCP Console でベースイメージビルドトリガーを手動実行

### 3. 通常のデプロイ

通常のコードデプロイでは、事前に作成されたベースイメージが使用され、ビルド時間が大幅に短縮されます（20 分 → 2-3 分程度）。

```bash
# 通常のpush（mainブランチ）でアプリケーションがデプロイされる
git push origin main
```

## アーキテクチャ

```
ベースイメージ（手動更新）:
python:3.13-slim + TeX Live Full + uv
           ↓
アプリケーションイメージ（自動更新）:
ベースイメージ + 依存関係 + アプリケーションコード
```

## トラブルシューティング

### ベースイメージが見つからない場合

Dockerfile でフォールバック機能を実装しているため、ベースイメージが存在しない場合は`python:3.13-slim`から直接ビルドされます。

### ビルド時間が長い場合

- ベースイメージが最新かどうか確認
- Cloud Build のマシンタイプ設定を確認（E2_HIGHCPU_8 を使用）
