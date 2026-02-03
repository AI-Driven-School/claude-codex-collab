# API Endpoints Specification

## Auth
- `POST /api/v1/auth/login`: JWTトークン発行
- `POST /api/v1/auth/register`: 企業・ユーザー登録

## Stress Check
- `GET /api/v1/stress-check/questions`: 57項目取得
- `POST /api/v1/stress-check/submit`: 回答送信・スコアリング

## Chat & AI Analysis
- `POST /api/v1/chat/webhook`: Slack/TeamsからのWebhook受け口
- `POST /api/v1/analysis/daily`: 日次データの集計リクエスト

## Dashboard
- `GET /api/v1/dashboard/company/{company_id}`: 会社全体の統計データ取得
- `GET /api/v1/dashboard/alerts`: 高ストレスアラート一覧取得
