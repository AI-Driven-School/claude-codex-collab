# タスク2: 認証API

## 要件

FastAPI + Python で以下を実装:

1. POST /auth/register（ユーザー登録）
2. POST /auth/login（JWT発行）
3. POST /auth/refresh（トークン更新）
4. POST /auth/logout（トークン無効化）
5. パスワードはbcryptでハッシュ化

## 成果物

- `app/routers/auth.py`
- `app/models/user.py`
- `app/utils/jwt.py`

## 評価基準

- セキュリティ（httpOnly Cookie, CSRF対策）
- エラーハンドリング
- コード品質
