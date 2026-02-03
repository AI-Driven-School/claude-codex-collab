# テスト実行ガイド

## 前提条件

1. **Supabase CloudまたはローカルPostgreSQLが利用可能であること**
   - Supabase Cloudの場合は `DATABASE_URL` を設定
   - ローカルの場合は `docker-compose up -d` で起動

2. **必要なポートが空いていること**
   - ポート3000: フロントエンド
   - ポート8000: バックエンド
   - ポート5432: PostgreSQL（ローカル運用時）
   - ポート27017: MongoDB

## セットアップ手順

### 1. データベース準備

Supabase Cloudを使う場合は `DATABASE_URL` を設定してください。
ローカルPostgreSQLを使う場合は以下を実行:

```bash
docker-compose up -d
```

### 2. バックエンドセットアップ

```bash
cd backend

# 仮想環境作成（初回のみ）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集:
# - DATABASE_URL=... (Supabase Cloud推奨)
# - OPENAI_API_KEY=sk-... (チャット機能を使用する場合)
# - JWT_SECRET_KEY=your-secret-key-change-in-production

# データベースマイグレーション
alembic upgrade head

# テストデータ作成
python scripts/seed_test_data.py
```

### 3. フロントエンドセットアップ

```bash
cd frontend

# 依存関係インストール
npm install

# 環境変数確認
# .envファイルに NEXT_PUBLIC_API_URL=http://localhost:8000 が設定されていることを確認
```

### 4. Playwrightセットアップ

```bash
# ルートディレクトリで
npm install
npx playwright install
```

## テスト実行

### 開発モードで実行

**ターミナル1: バックエンド**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**ターミナル2: フロントエンド**
```bash
cd frontend
npm run dev
```

**ターミナル3: テスト実行**
```bash
npm run test:e2e
```

### UIモードで実行（推奨）

```bash
npm run test:e2e:ui
```

### ヘッドモードで実行

```bash
npm run test:e2e:headed
```

### 特定のテストファイルのみ実行

```bash
npx playwright test tests/e2e/auth.spec.ts
npx playwright test tests/e2e/stress-check.spec.ts
npx playwright test tests/e2e/chat.spec.ts
npx playwright test tests/e2e/dashboard.spec.ts
```

## テストデータ

テスト用のユーザーアカウント:

- **管理者**: 
  - メール: `admin@example.com`
  - パスワード: `password123`

- **従業員**: 
  - メール: `employee@example.com`
  - パスワード: `password123`

これらのユーザーは `backend/scripts/seed_test_data.py` を実行することで作成されます。

## トラブルシューティング

### データベース接続エラー

```bash
# Dockerコンテナの状態を確認
docker ps

# コンテナを再起動
docker-compose restart

# ログを確認
docker-compose logs postgres
```

### ポート競合エラー

既にポートが使用されている場合:

1. 使用中のプロセスを確認:
   ```bash
   lsof -i :3000  # フロントエンド
   lsof -i :8000  # バックエンド
   ```

2. プロセスを終了するか、ポートを変更

### マイグレーションエラー

```bash
cd backend
alembic downgrade -1  # 1つ前のバージョンに戻す
alembic upgrade head  # 最新バージョンにアップグレード
```

### テストがタイムアウトする

`playwright.config.ts`の`timeout`を増やすか、テストの待機時間を調整してください。

### OpenAI APIエラー

チャット機能のテストでエラーが出る場合:

1. `.env`ファイルに`OPENAI_API_KEY`が設定されているか確認
2. APIキーが有効か確認
3. レート制限に達していないか確認

## テストカバレッジ

現在のテストカバレッジ:

- ✅ 認証機能（正常系・異常系）
- ✅ ストレスチェック機能（正常系・異常系）
- ✅ チャット機能（正常系・異常系）
- ✅ ダッシュボード機能（正常系・異常系）

## 注意事項

1. **レート制限テスト**: チャットのレート制限テストは10回のメッセージ送信を行うため、時間がかかります。

2. **ネットワークエラーテスト**: 一部のテストはネットワークをオフラインに設定するため、テスト後にオンラインに戻します。

3. **データベース状態**: テスト実行後、データベースの状態が変更される可能性があります。必要に応じてテストデータを再作成してください。

4. **並列実行**: テストは並列実行されるため、データベースの競合が発生する可能性があります。問題がある場合は、`playwright.config.ts`の`workers`を1に設定してください。
