# StressAgent Pro - デプロイ手順書

## 概要

本ドキュメントでは、StressAgent Proの本番環境へのデプロイ手順を説明します。

- **バックエンド**: Railway
- **フロントエンド**: Vercel
- **データベース**: Railway PostgreSQL

---

## 前提条件

- GitHub アカウント
- Railway アカウント (https://railway.app)
- Vercel アカウント (https://vercel.com)

---

## 1. バックエンドデプロイ (Railway)

### 1.1 Railway プロジェクト作成

1. Railway にログイン
2. 「New Project」→「Deploy from GitHub repo」
3. リポジトリを選択し、`backend` ディレクトリを指定

### 1.2 PostgreSQL 追加

1. プロジェクト内で「+ New」→「Database」→「PostgreSQL」
2. 自動的に `DATABASE_URL` が設定される

### 1.3 環境変数設定

Railway の Variables タブで以下を設定:

```
JWT_SECRET_KEY=<openssl rand -hex 32 で生成>
DEBUG_MODE=false
CORS_ALLOW_ORIGINS=https://your-frontend.vercel.app
COOKIE_SECURE=true
COOKIE_SAMESITE=none
OPENAI_API_KEY=<your-api-key>
```

### 1.4 デプロイ確認

```bash
curl https://your-backend.railway.app/health
# {"status": "ok"}
```

---

## 2. フロントエンドデプロイ (Vercel)

### 2.1 Vercel プロジェクト作成

1. Vercel にログイン
2. 「New Project」→ GitHub リポジトリを選択
3. Root Directory: `frontend`
4. Framework Preset: Next.js

### 2.2 環境変数設定

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 2.3 デプロイ

自動デプロイが有効。`main` ブランチへの push で自動デプロイ。

---

## 3. GitHub Actions シークレット設定

リポジトリの Settings → Secrets and variables → Actions:

### バックエンド用
- `RAILWAY_TOKEN`: Railway API トークン

### フロントエンド用
- `VERCEL_TOKEN`: Vercel API トークン
- `VERCEL_ORG_ID`: Vercel 組織 ID
- `VERCEL_PROJECT_ID`: Vercel プロジェクト ID
- `NEXT_PUBLIC_API_URL`: バックエンド URL

---

## 4. DNS / カスタムドメイン設定

### Railway
1. Settings → Domains
2. 「Generate Domain」または カスタムドメインを追加
3. DNS に CNAME レコードを設定

### Vercel
1. Settings → Domains
2. カスタムドメインを追加
3. DNS に指示された設定を追加

---

## 5. 本番環境チェックリスト

- [ ] JWT_SECRET_KEY が安全な値に設定されている
- [ ] DEBUG_MODE=false に設定されている
- [ ] COOKIE_SECURE=true に設定されている
- [ ] CORS_ALLOW_ORIGINS が本番フロントエンドのみに制限されている
- [ ] SSL/TLS が有効になっている
- [ ] データベースバックアップが設定されている
- [ ] モニタリング/アラートが設定されている

---

## 6. トラブルシューティング

### バックエンドが起動しない

```bash
# ログを確認
railway logs
```

よくある原因:
- `JWT_SECRET_KEY` が設定されていない
- `DATABASE_URL` が正しくない

### CORS エラー

- `CORS_ALLOW_ORIGINS` にフロントエンドの完全な URL を設定
- `COOKIE_SAMESITE=none` と `COOKIE_SECURE=true` を設定

### データベース接続エラー

- Railway PostgreSQL の接続文字列を確認
- `?sslmode=require` が付いているか確認

---

## 7. ロールバック手順

### Railway
1. Deployments タブで以前のデプロイを選択
2. 「Redeploy」をクリック

### Vercel
1. Deployments タブで以前のデプロイを選択
2. 「...」→「Promote to Production」
