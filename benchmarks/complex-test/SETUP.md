# セットアップガイド（Supabase Cloud / Resend 対応）

## 1. 環境準備

### 必要なツール
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- npm または yarn

## 2. データベース準備（Supabase Cloud）

- Supabase CloudのPostgreSQLを使用します。
- `DATABASE_URL` にSupabaseの接続URLを設定してください。
  - 例: `postgresql+asyncpg://USER:PASSWORD@HOST:PORT/postgres?sslmode=require`

## 3. バックエンドセットアップ

```bash
cd backend

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定（例: backend/.env）
# - DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/postgres?sslmode=require
# - JWT_SECRET_KEY=ランダムな文字列
# - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
# - JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
# - COOKIE_SECURE=true（本番はtrue）
# - COOKIE_SAMESITE=none（別ドメイン運用時）
# - COOKIE_DOMAIN=example.com（必要な場合）
# - CORS_ALLOW_ORIGINS=https://your-frontend-domain
# - OPENAI_API_KEY=（AI機能利用時）
# - EMAIL_PROVIDER=resend
# - RESEND_API_KEY=（Resend APIキー）
# - EMAIL_FROM=noreply@your-domain
# - EMAIL_FROM_NAME=StressAgent Pro

# データベースマイグレーション
alembic revision --autogenerate -m "Initial migration"  # 初回のみ
alembic upgrade head

# テストデータのシード（オプション）
python scripts/seed_test_data.py

# サーバー起動
uvicorn app.main:app --reload --port 8000
```

## 4. フロントエンドセットアップ

```bash
cd frontend

# 依存関係インストール
npm install

# 環境変数設定（例: frontend/.env）
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 開発サーバー起動
npm run dev
```

## 5. E2Eテスト実行

```bash
# ルートディレクトリで
npm install
npx playwright install

# テスト実行
npm run test:e2e

# UIモードで実行
npm run test:e2e:ui

# ヘッドモードで実行
npm run test:e2e:headed
```

## 6. テストデータ

テスト用のユーザー:
- **管理者**: admin@example.com / password123
- **従業員**: employee@example.com / password123

これらのユーザーは `scripts/seed_test_data.py` を実行することで作成されます。

## トラブルシューティング

### データベース接続エラー
- Dockerコンテナが起動しているか確認: `docker ps`
- データベースURLが正しいか確認

### ポート競合
- バックエンド: 8000番ポート
- フロントエンド: 3000番ポート
- 既に使用されている場合は変更してください

### マイグレーションエラー
- データベースが起動しているか確認
- `alembic upgrade head` を再実行
