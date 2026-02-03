# StressAgent Pro

AI駆動型メンタルヘルスSaaSアプリケーション

[![CI](https://github.com/your-org/stressagent-pro/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/stressagent-pro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 概要

StressAgent Proは、企業の従業員メンタルヘルスを支援するAI駆動型SaaSです。

### 主な機能

- **ストレスチェック**: 厚生労働省ガイドライン準拠の57問調査
- **AIカウンセリング**: OpenAI GPT-4を活用した24時間対応チャットボット
- **管理者ダッシュボード**: 部署別ストレス状況の可視化・ヒートマップ表示
- **AI改善提案**: データに基づく具体的な職場環境改善提案
- **マルチプラットフォーム連携**: Slack / Teams / LINE / Discord

## 技術スタック

| レイヤー | 技術 |
|----------|------|
| フロントエンド | Next.js 14, React 18, TypeScript, Tailwind CSS |
| バックエンド | FastAPI, Python 3.11, SQLAlchemy |
| データベース | PostgreSQL |
| AI | OpenAI GPT-4o-mini |
| 認証 | JWT (HttpOnly Cookie) |
| デプロイ | Vercel (Frontend), Railway (Backend) |

## クイックスタート

### 前提条件

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/stressagent-pro.git
cd stressagent-pro

# バックエンド
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env を編集してJWT_SECRET_KEY等を設定
# JWT_SECRET_KEY生成: openssl rand -hex 32

# データベースマイグレーション
alembic upgrade head

# フロントエンド
cd ../frontend
npm install
cp .env.example .env.local
```

### 起動

```bash
# バックエンド (ターミナル1)
cd backend
uvicorn app.main:app --reload --port 8000

# フロントエンド (ターミナル2)
cd frontend
npm run dev
```

- フロントエンド: http://localhost:3000
- API ドキュメント: http://localhost:8000/docs

## ドキュメント

| ドキュメント | 説明 |
|-------------|------|
| [開発環境構築](docs/DEVELOPMENT.md) | ローカル開発環境のセットアップ手順 |
| [アーキテクチャ](docs/ARCHITECTURE.md) | システム設計・構成図 |
| [API リファレンス](docs/API.md) | REST API エンドポイント一覧 |
| [デプロイ手順](docs/DEPLOYMENT.md) | 本番環境へのデプロイ方法 |

## ディレクトリ構成

```
.
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── routers/         # API エンドポイント
│   │   ├── services/        # ビジネスロジック
│   │   ├── models/          # Pydantic スキーマ
│   │   ├── db/              # データベース設定・モデル
│   │   └── utils/           # ユーティリティ
│   └── tests/               # テスト
├── frontend/                # Next.js フロントエンド
│   ├── app/                 # App Router ページ
│   ├── components/          # React コンポーネント
│   └── lib/                 # API クライアント等
├── docs/                    # ドキュメント
└── .github/workflows/       # CI/CD
```

## セキュリティ

- JWT認証（HttpOnly Cookie）
- パスワード複雑性要件（大文字・小文字・数字・特殊文字）
- レート制限（slowapi）
- PII（個人情報）フィルタリング
- CORS制限

## テスト

```bash
# バックエンド
cd backend
pytest tests/ -v

# フロントエンド
cd frontend
npm test
```

## コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

[MIT License](LICENSE)

## 注意事項

- 本ソフトウェアは医療診断を行うものではありません
- 深刻なメンタルヘルスの問題がある場合は、専門家にご相談ください
