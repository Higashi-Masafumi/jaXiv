# JAXiV デプロイメント ガイド

このドキュメントでは、JAXiV アプリケーションを **Terraform + Cloud Build CI/CD** で GCP Cloud Run にデプロイする手順を説明します。

## 🚨 重要: エラー修正済み

以下のエラーを修正済みです：

- Cloud Run v2 の`PORT`環境変数エラー（システム自動設定のため削除）
- プロジェクト ID の形式エラー（数字 → 文字列形式に修正）
- Cloud Build トリガーの順序エラー（GitHub 連携後に設定）

## 手順 1: 正しい環境変数の設定

```bash
# 正しいプロジェクトID（文字列形式）を使用
export TF_VAR_project_id="jaxiv-465416"
export TF_VAR_supabase_url="https://your-project.supabase.co"
export TF_VAR_supabase_key="your-supabase-anon-key"
export TF_VAR_database_url="postgresql://user:password@host:port/database"
```

## 手順 2: Terraform でインフラをデプロイ

```bash
cd terraform

# 初期化
terraform init

# プラン確認
terraform plan

# デプロイ実行（「yes」と入力）
terraform apply
```

**📝 注意**:

- `Do you want to perform these actions?` には必ず **`yes`** と入力
- Cloud Build トリガーは手動で後から設定します

## 手順 3: GitHub 連携の設定

### 3-1. GCP コンソールで GitHub 連携

1. **[GCP Cloud Build](https://console.cloud.google.com/cloud-build/triggers)** にアクセス
2. **「リポジトリを接続」** をクリック
3. **GitHub** を選択し、認証
4. **リポジトリ（Higashi-Masafumi/jaXiv）** を接続

### 3-2. Cloud Build トリガーの作成

GCP コンソールで以下の設定でトリガーを作成：

- **名前**: `jaxiv-main-trigger`
- **イベント**: `mainブランチにプッシュ`
- **ソース**: `Higashi-Masafumi/jaXiv`
- **構成**: `cloudbuild.yaml`
- **サービスアカウント**: `jaxiv-cloud-build@jaxiv-465416.iam.gserviceaccount.com`

## 手順 4: 初回デプロイテスト

```bash
# 変更をコミット・プッシュ
git add .
git commit -m "Setup CI/CD pipeline"
git push origin main
```

## 手順 5: サービス URL の確認

```bash
cd terraform
terraform output backend_url
terraform output frontend_url
```

## 必須環境変数

| 変数名                | 説明                 | 例                                    |
| --------------------- | -------------------- | ------------------------------------- |
| `TF_VAR_project_id`   | GCP プロジェクト ID  | `jaxiv-465416`                        |
| `TF_VAR_supabase_url` | Supabase URL         | `https://xxx.supabase.co`             |
| `TF_VAR_supabase_key` | Supabase 匿名キー    | `eyJhbGciOiJIUzI1...`                 |
| `TF_VAR_database_url` | データベース接続 URL | `postgresql://user:pass@host:5432/db` |

## トラブルシューティング

### 修正済みエラー

1. **✅ PORT 環境変数エラー**: Cloud Run v2 では`PORT`を手動設定不可（修正済み）
2. **✅ プロジェクト番号エラー**: 数字形式から文字列形式に修正（修正済み）
3. **✅ リポジトリマッピングエラー**: GitHub 連携を先に行う手順に変更（修正済み）

### よくある問題

1. **Terraform apply 時の入力エラー**

   - `Do you want to perform these actions?` には必ず **`yes`** と入力

2. **GitHub 連携エラー**

   - GCP コンソールで GitHub の認証が完了しているか確認
   - リポジトリの権限設定を確認

3. **Cloud Build 権限エラー**
   - サービスアカウント: `jaxiv-cloud-build@jaxiv-465416.iam.gserviceaccount.com`
   - Terraform で自動的に必要な権限が付与済み

### ログの確認

```bash
# Cloud Buildのログ
gcloud builds list
gcloud builds log [BUILD_ID]

# Cloud Runのログ
gcloud logs read --limit=50 --filter="resource.type=cloud_run_revision"
```

## リソースの削除

```bash
cd terraform
terraform destroy
```

**⚠️ 注意**: この操作により、Cloud Run サービスや Artifact Registry、Secret Manager のデータも削除されます。
