# AGENTS.md - AI Agent Collaboration Guide

このファイルはClaude Code / OpenAI Codex / 他のAIエージェントが共同作業するためのガイドです。

## プロジェクト概要

**StressAgent Pro** - AI駆動型メンタルヘルスSaaS

- **バックエンド**: FastAPI (Python 3.11+)
- **フロントエンド**: Next.js 14 (TypeScript)
- **データベース**: PostgreSQL (Supabase)
- **認証**: JWT + httpOnly Cookie
- **AI**: OpenAI GPT-4

## ディレクトリ構造

```
/
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── db/             # データベースモデル・接続
│   │   ├── models/         # Pydanticスキーマ
│   │   ├── routers/        # APIエンドポイント
│   │   ├── services/       # ビジネスロジック
│   │   └── utils/          # ユーティリティ
│   ├── alembic/            # DBマイグレーション
│   └── scripts/            # スクリプト
├── frontend/               # Next.js フロントエンド
│   ├── app/                # App Router ページ
│   ├── components/         # UIコンポーネント
│   └── lib/                # API クライアント・ユーティリティ
└── tests/                  # E2Eテスト (Playwright)
```

## 開発ルール

### コーディング規約

- **言語**: 日本語コメント可、変数名・関数名は英語
- **インデント**: 2スペース (TypeScript), 4スペース (Python)
- **命名規則**:
  - Python: snake_case
  - TypeScript: camelCase (変数・関数), PascalCase (コンポーネント・型)

### API設計

- RESTful設計
- エンドポイント: `/api/v1/{resource}`
- 認証必須エンドポイントは `Depends(get_current_user)` を使用

### データベース

- SQLAlchemy AsyncSession使用
- マイグレーション: `alembic revision --autogenerate -m "message"`
- モデル定義: `backend/app/db/models.py`

## 現在の実装状況

### 完了済み機能
- ✅ 認証（ログイン・登録・JWT）
- ✅ ストレスチェック（57項目）
- ✅ AIチャット（感情分析付き）
- ✅ 管理者ダッシュボード
- ✅ 部署管理CRUD
- ✅ PDFレポート生成
- ✅ Slack/Teams連携
- ✅ チャット履歴DB永続化

### 主要ファイル

| 機能 | バックエンド | フロントエンド |
|------|-------------|---------------|
| 認証 | `routers/auth.py` | `app/login/`, `app/register/` |
| ストレスチェック | `routers/stress_check.py` | `app/stress-check/` |
| チャット | `routers/chat.py` | `app/chat/` |
| ダッシュボード | `routers/dashboard.py` | `app/dashboard/` |
| 管理 | `routers/admin.py` | `app/admin/` |

## タスク管理

作業前に `TODO.md` を確認・更新してください。

```markdown
## 進行中のタスク
- [ ] タスク名 (@担当エージェント)

## 完了タスク
- [x] タスク名 (@担当エージェント) - 完了日
```

## コマンド

```bash
# バックエンド起動
cd backend && uvicorn app.main:app --reload --port 8000

# フロントエンド起動
cd frontend && npm run dev

# マイグレーション実行
cd backend && alembic upgrade head

# テスト実行
npm run test:e2e

# 型チェック
cd frontend && npm run type-check
```

## 環境変数

### バックエンド (`backend/.env`)
- `DATABASE_URL` - PostgreSQL接続文字列
- `JWT_SECRET_KEY` - JWT署名キー
- `OPENAI_API_KEY` - OpenAI APIキー
- `SLACK_WEBHOOK_URL` - Slack通知用
- `TEAMS_WEBHOOK_URL` - Teams通知用

### フロントエンド (`frontend/.env.local`)
- `NEXT_PUBLIC_API_URL` - バックエンドURL

## エージェント間の連携ルール

1. **作業開始時**: `TODO.md` に担当タスクを記載
2. **ファイル編集時**: 同時編集を避けるため、作業ファイルを明記
3. **作業完了時**: `TODO.md` を更新、変更内容をコミットメッセージに記載
4. **競合発生時**: 最新のgit状態を確認してから作業再開

## Claude Code → Codex タスク委譲

Claude Codeがメインエージェントとして、Codexにタスクを委譲できます。

### タスクを委譲する

```bash
./scripts/delegate-to-codex.sh "タスクの説明をここに書く"
```

### タスク状態を確認する

```bash
# 最新タスクの状態確認
./scripts/check-codex-task.sh

# 特定タスクの状態確認
./scripts/check-codex-task.sh 20240201-143022
```

### タスクファイルの場所

- タスク一覧: `.codex-tasks/`
- タスク定義: `.codex-tasks/task-{ID}.md`
- Codex出力: `.codex-tasks/output-{ID}.md`
- 実行ログ: `.codex-tasks/log-{ID}.txt`

### 推奨タスク分担

| タスク種別 | 担当 | 理由 |
|-----------|------|------|
| 設計・計画 | Claude Code | コンテキスト理解が重要 |
| 単純実装 | Codex | 並列実行可能 |
| コードレビュー | Codex | `codex review` コマンドあり |
| テスト作成 | Codex | 定型作業 |
| ドキュメント | どちらでも | - |
| デバッグ | Claude Code | 対話的な調査が必要 |

## 注意事項

- 本番環境の認証情報は `.env` に記載（gitignore済み）
- 破壊的なDB操作前は必ずバックアップ確認
- セキュリティに関わる変更は慎重に
