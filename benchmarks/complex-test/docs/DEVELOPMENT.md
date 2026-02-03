# StressAgent Pro - 開発環境構築ガイド

## 前提条件

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker（オプション）

---

## 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/stressagent-pro.git
cd stressagent-pro
```

---

## 2. バックエンドセットアップ

### 2.1 仮想環境の作成

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2.2 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2.3 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/stressagent
JWT_SECRET_KEY=your-secret-key  # openssl rand -hex 32 で生成
DEBUG_MODE=true
OPENAI_API_KEY=sk-...
```

### 2.4 データベースのセットアップ

```bash
# PostgreSQLでデータベース作成
createdb stressagent

# マイグレーション実行
alembic upgrade head
```

### 2.5 開発サーバーの起動

```bash
uvicorn app.main:app --reload --port 8000
```

API ドキュメント: http://localhost:8000/docs

---

## 3. フロントエンドセットアップ

### 3.1 依存関係のインストール

```bash
cd frontend
npm ci
```

### 3.2 環境変数の設定

```bash
cp .env.example .env.local
```

`.env.local` を編集:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3.3 開発サーバーの起動

```bash
npm run dev
```

アプリケーション: http://localhost:3000

---

## 4. Docker を使用した開発

### 4.1 全サービスの起動

```bash
docker-compose up -d
```

### 4.2 個別サービスの起動

```bash
# PostgreSQL のみ
docker-compose up -d db

# バックエンドのみ
docker-compose up -d backend
```

---

## 5. テストの実行

### バックエンド

```bash
cd backend
pytest tests/ -v
pytest tests/ -v --cov=app  # カバレッジ付き
```

### フロントエンド

```bash
cd frontend
npm test
npm run test:coverage  # カバレッジ付き
```

---

## 6. コード品質チェック

### バックエンド

```bash
# Lint
flake8 app/

# フォーマット
black app/
isort app/
```

### フロントエンド

```bash
npm run lint
npm run type-check
```

---

## 7. よくある問題と解決策

### PostgreSQL 接続エラー

```
asyncpg.exceptions.ConnectionRefusedError
```

**解決策**: PostgreSQL が起動しているか確認
```bash
pg_ctl status
# または
brew services list  # macOS
```

### JWT シークレット未設定エラー

```
RuntimeError: JWT_SECRET_KEY environment variable is required
```

**解決策**: `.env` ファイルに `JWT_SECRET_KEY` を設定
```bash
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### Node.js バージョンエラー

**解決策**: Node.js 20 以上を使用
```bash
nvm install 20
nvm use 20
```

---

## 8. 開発フロー

1. `feature/xxx` ブランチを作成
2. 変更を実装
3. テストを追加・実行
4. Lint チェック
5. PR を作成
6. レビュー後マージ
