-- StressAIAgent テーブル作成SQL
-- Supabase SQL Editorで実行してください

-- プラン種別ENUM
CREATE TYPE plan_type AS ENUM ('basic', 'premium');

-- ユーザーロールENUM
CREATE TYPE user_role AS ENUM ('admin', 'employee', 'doctor');

-- 企業テーブル
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    industry VARCHAR,
    plan_type plan_type NOT NULL DEFAULT 'basic',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 部署テーブル
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    name VARCHAR NOT NULL,
    description VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    department_id UUID REFERENCES departments(id),
    email VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    role user_role NOT NULL DEFAULT 'employee',
    slack_id VARCHAR,
    line_user_id VARCHAR,
    link_code VARCHAR UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_line_user_id ON users(line_user_id);

-- ストレスチェックテーブル
CREATE TABLE IF NOT EXISTS stress_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    period DATE NOT NULL,
    answers JSONB NOT NULL,
    total_score INTEGER NOT NULL,
    is_high_stress BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 日次スコアテーブル
CREATE TABLE IF NOT EXISTS daily_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    sentiment_score FLOAT NOT NULL,
    fatigue_level INTEGER,
    sleep_hours FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 途中保存テーブル
CREATE TABLE IF NOT EXISTS draft_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    answers JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- テストデータ: テスト企業とアカウント
INSERT INTO companies (id, name, industry, plan_type)
VALUES ('00000000-0000-0000-0000-000000000001', 'テスト株式会社', 'IT', 'basic')
ON CONFLICT DO NOTHING;

-- テストユーザー (パスワード: testpass123)
-- bcryptハッシュ: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.PQxqQw.8KP6Gie
INSERT INTO users (id, company_id, email, hashed_password, role)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'test@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.PQxqQw.8KP6Gie',
    'admin'
)
ON CONFLICT DO NOTHING;

-- 確認
SELECT 'Tables created successfully!' as status;
SELECT * FROM users;
