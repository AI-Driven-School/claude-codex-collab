# StressAgent Pro - アーキテクチャ設計書

## 概要

StressAgent Pro は AI 駆動型メンタルヘルス SaaS アプリケーションです。

---

## システム構成

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (Next.js / React)                         │
│                      Vercel にデプロイ                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│                    (FastAPI / Python)                        │
│                     Railway にデプロイ                        │
├─────────────────────────┬───────────────────────────────────┤
│                         │                                    │
│  ┌──────────────┐  ┌────┴────┐  ┌──────────────┐           │
│  │  認証サービス │  │ API     │  │ AIサービス    │           │
│  │  (JWT)       │  │ ルーター │  │ (OpenAI)     │           │
│  └──────────────┘  └─────────┘  └──────────────┘           │
│                                                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │   MongoDB   │  │  OpenAI API │
│ (メインDB)   │  │ (チャット履歴)│  │  (AI分析)   │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## ディレクトリ構成

### バックエンド

```
backend/
├── app/
│   ├── main.py              # エントリーポイント
│   ├── db/
│   │   ├── database.py      # DB接続設定
│   │   └── models.py        # SQLAlchemy モデル
│   ├── models/              # Pydantic スキーマ
│   ├── routers/             # API エンドポイント
│   ├── services/            # ビジネスロジック
│   └── utils/               # ユーティリティ
├── tests/                   # テスト
├── alembic/                 # マイグレーション
└── requirements.txt
```

### フロントエンド

```
frontend/
├── app/                     # Next.js App Router
│   ├── (auth)/              # 認証ページ
│   ├── dashboard/           # 管理者ダッシュボード
│   └── home/                # ユーザーホーム
├── components/              # 共通コンポーネント
├── lib/
│   └── api/                 # API クライアント
└── public/                  # 静的ファイル
```

---

## データモデル

### 主要エンティティ

```
Company (企業)
├── id: UUID
├── name: string
├── industry: string
└── plan_type: enum

User (ユーザー)
├── id: UUID
├── company_id: UUID (FK)
├── department_id: UUID (FK)
├── email: string
├── role: enum (admin/employee)
└── hashed_password: string

Department (部署)
├── id: UUID
├── company_id: UUID (FK)
└── name: string

StressCheck (ストレスチェック)
├── id: UUID
├── user_id: UUID (FK)
├── answers: JSON
├── total_score: float
├── is_high_stress: boolean
└── created_at: datetime
```

---

## 認証フロー

```
1. ログイン
   Client → POST /api/v1/auth/login
         ← Set-Cookie: access_token, refresh_token

2. API リクエスト
   Client → GET /api/v1/dashboard (Cookie: access_token)
         ← 200 OK + データ

3. トークンリフレッシュ
   Client → POST /api/v1/auth/refresh (Cookie: refresh_token)
         ← Set-Cookie: 新しい access_token, refresh_token
```

---

## セキュリティ対策

| 対策 | 実装 |
|------|------|
| 認証 | JWT (HttpOnly Cookie) |
| パスワード | bcrypt ハッシュ化 |
| CORS | オリジン制限 |
| レート制限 | slowapi (5-30 req/min) |
| PII 保護 | AI 送信前にフィルタリング |
| SQL インジェクション | SQLAlchemy ORM |

---

## パフォーマンス最適化

### フロントエンド
- React.memo / useMemo で再レンダリング抑制
- 画像最適化 (next/image)
- コード分割 (動的インポート)

### バックエンド
- N+1 クエリ対策（サブクエリ使用）
- 非同期処理 (async/await)
- コネクションプーリング

---

## 外部サービス連携

| サービス | 用途 |
|----------|------|
| OpenAI API | 感情分析・改善提案生成 |
| Slack/Teams | 通知連携 |
| LINE/Discord | チャットボット |
| SendGrid/Resend | メール送信 |
