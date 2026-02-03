# Technical Specification

## System Architecture

### Frontend (Next.js)
- `app/`: App Router使用
- `components/ui/`: Shadcn/UI コンポーネント
- `lib/api/`: Backend APIとの通信クライアント (Axios/Fetch)
- 認証: NextAuth.js (Cognito または Auth0 連携想定、MVPはJWT独自実装も可)

### Backend (FastAPI)
- `app/main.py`: エントリーポイント
- `app/routers/`: エンドポイント定義 (users, stress-check, chat, analysis)
- `app/models/`: Pydanticモデル (Request/Response定義)
- `app/db/`: SQLAlchemyモデル & DB接続
- `app/services/`: ビジネスロジック (AI分析、スコアリング計算)

### AI Service Layer
- **LLM**: OpenAI GPT-4o-mini (コストパフォーマンス重視)
- **Prompt Engineering**: System Promptで「産業カウンセラー」のペルソナを設定。
- **Privacy**: PII除去フィルターを通してからOpenAI APIへ送信。

## Data Flow
1. **User Input** -> Frontend/Slack -> Backend API
2. **Processing** -> PII Masking -> OpenAI API -> Sentiment Analysis
3. **Storage** -> PostgreSQL (Structured Data) + MongoDB (Chat Logs)
4. **Visualization** -> Next.js Dashboard (Recharts使用)

## Security
- 通信: 全てHTTPS (TLS 1.2+)
- DB: AWS RDS (PostgreSQL) 暗号化有効
- 保存期間: ログデータは同意に基づき一定期間で匿名化処理
