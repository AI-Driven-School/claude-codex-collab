# Database Schema Design

## Relational Database (PostgreSQL)

### `companies`
- id: UUID (PK)
- name: VARCHAR
- industry: VARCHAR (業種)
- plan_type: ENUM ('basic', 'premium')

### `users`
- id: UUID (PK)
- company_id: UUID (FK)
- email: VARCHAR (Unique)
- hashed_password: VARCHAR
- role: ENUM ('admin', 'employee', 'doctor')
- slack_id: VARCHAR (Nullable)

### `stress_checks` (年1回の正式検査)
- id: UUID (PK)
- user_id: UUID (FK)
- period: DATE (実施年月)
- answers: JSONB (57項目の回答データ: { "q1": 4, "q2": 2... })
- total_score: INTEGER
- is_high_stress: BOOLEAN
- created_at: TIMESTAMP

### `daily_scores` (AI推論結果)
- id: UUID (PK)
- user_id: UUID (FK)
- date: DATE
- sentiment_score: FLOAT (-1.0 to 1.0)
- fatigue_level: INTEGER (1-5)
- sleep_hours: FLOAT

## NoSQL (MongoDB)

### `chat_logs`
- _id: ObjectId
- user_id: UUID
- platform: 'slack' | 'teams'
- timestamp: ISODate
- message_content: String (Encrypted)
- ai_response: String
- interaction_tags: Array<String> ['workload', 'human_relations']
