# StressAgent Pro - API リファレンス

## 概要

- **ベース URL**: `https://api.stressagent.example.com`
- **認証**: JWT (Cookie-based)
- **フォーマット**: JSON

API ドキュメント（OpenAPI）: `/docs`

---

## 認証 API

### POST /api/v1/auth/register

企業・管理者ユーザーの新規登録

**Request Body**:
```json
{
  "email": "admin@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "company_name": "株式会社サンプル",
  "industry": "IT",
  "plan_type": "basic"
}
```

**Response**: `200 OK`
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "role": "admin",
    "company_id": "uuid"
  }
}
```

---

### POST /api/v1/auth/login

ログイン

**Request Body**:
```json
{
  "email": "admin@example.com",
  "password": "SecurePass123!"
}
```

**Response**: `200 OK` + Set-Cookie

---

### POST /api/v1/auth/logout

ログアウト

**Response**: `200 OK`
```json
{
  "message": "logged_out"
}
```

---

### GET /api/v1/auth/me

現在のユーザー情報取得

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "admin@example.com",
  "role": "admin",
  "company_id": "uuid",
  "company_name": "株式会社サンプル"
}
```

---

## ダッシュボード API

### GET /api/v1/dashboard/company/{company_id}

会社の統計データを取得

**Query Parameters**:
- `department_id` (optional): 部署でフィルター
- `period` (optional): `thisMonth`, `lastMonth`, `3months`, `6months`, `1year`, `all`
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD

**Response**: `200 OK`
```json
{
  "stats": {
    "total_employees": 100,
    "high_stress_count": 15,
    "stress_check_completion_rate": 85.0,
    "average_stress_score": 52.3
  },
  "department_stats": [
    {
      "department_name": "営業部",
      "average_score": 65.2,
      "high_stress_count": 5,
      "employee_count": 30
    }
  ],
  "alerts": [],
  "recommendations": []
}
```

---

## ストレスチェック API

### POST /api/v1/stress-check/submit

ストレスチェック回答を送信

**Request Body**:
```json
{
  "answers": {
    "q1": 3,
    "q2": 4,
    "q3": 2
  },
  "period": "2024-04-01"
}
```

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "total_score": 145,
  "is_high_stress": false,
  "scores": {
    "job_stress_score": 2.5,
    "stress_reaction_score": 2.0,
    "support_score": 3.2,
    "satisfaction_score": 3.0
  }
}
```

---

## 部署 API

### GET /api/v1/departments

部署一覧を取得

**Response**: `200 OK`
```json
{
  "departments": [
    {
      "id": "uuid",
      "name": "営業部"
    }
  ]
}
```

### POST /api/v1/departments

部署を作成（管理者のみ）

**Request Body**:
```json
{
  "name": "新規部署"
}
```

---

## エラーレスポンス

### 400 Bad Request
```json
{
  "detail": "パスワードが一致しません"
}
```

### 401 Unauthorized
```json
{
  "detail": "認証が必要です"
}
```

### 403 Forbidden
```json
{
  "detail": "アクセス権限がありません"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

---

## レート制限

| エンドポイント | 制限 |
|---------------|------|
| POST /auth/register | 5/分 |
| POST /auth/login | 10/分 |
| POST /auth/refresh | 30/分 |
| その他 | 60/分 |
