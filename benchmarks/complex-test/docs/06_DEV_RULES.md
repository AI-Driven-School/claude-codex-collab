# 開発ルール・コーディング規約

## 1. コーディング規約

### 1.1 言語・コメント
- **必須**: 全てのコメント、ドキュメント、コミットメッセージは日本語で記述
- **例外**: 外部ライブラリのAPI名や技術用語は英語のまま使用可

### 1.2 TypeScript (Frontend)
- `any`型の使用を**厳禁**
- 型定義は必ず明示的に記述
- 関数の戻り値型も必ず指定
- インターフェース名は`PascalCase`、変数名は`camelCase`
- コンポーネント名は`PascalCase`、ファイル名も`PascalCase.tsx`

```typescript
// ✅ Good
interface UserProfile {
  id: string;
  email: string;
}

const getUserProfile = async (userId: string): Promise<UserProfile> => {
  // ...
};

// ❌ Bad
const getUserProfile = async (userId: any) => {
  // ...
};
```

### 1.3 Python (Backend)
- Type Hintを**必須**とする
- 関数の引数・戻り値に型を明示
- クラス名は`PascalCase`、関数・変数名は`snake_case`
- モジュール名は`snake_case.py`

```python
# ✅ Good
from typing import Optional
from uuid import UUID

def get_user_profile(user_id: UUID) -> Optional[dict[str, Any]]:
    # ...
    pass

# ❌ Bad
def get_user_profile(user_id):
    # ...
    pass
```

### 1.4 エラーハンドリング
- **ユーザー向けエラーメッセージ**: 日本語で分かりやすく、技術的詳細は含めない
- **バックエンドログ**: 詳細なエラー情報（スタックトレース、リクエストID等）を記録
- エラーレスポンスは統一フォーマットを使用

```python
# ✅ Good
class APIError(Exception):
    def __init__(self, message: str, status_code: int, detail: Optional[str] = None):
        self.message = message  # ユーザー向け
        self.status_code = status_code
        self.detail = detail  # ログ用詳細情報
```

### 1.5 セキュリティ
- **PII（個人特定情報）の扱い**:
  - ログに個人名、メールアドレス、電話番号をそのまま出力しない
  - 必要に応じてマスキング処理（例: `user@example.com` → `u***@example.com`）
  - OpenAI APIへ送信する前にPIIクリーニングを実施
- **パスワード**: 必ずハッシュ化（bcrypt推奨）、平文保存は厳禁
- **認証トークン**: JWTの有効期限を適切に設定（デフォルト: 24時間）

## 2. ディレクトリ構造

### 2.1 Frontend (Next.js)
```
frontend/
├── app/                    # App Router
│   ├── (auth)/            # 認証関連ページ
│   ├── (dashboard)/       # ダッシュボード
│   └── api/               # API Routes（必要に応じて）
├── components/
│   ├── ui/                # Shadcn/UIコンポーネント
│   ├── features/          # 機能別コンポーネント
│   └── layouts/           # レイアウトコンポーネント
├── lib/
│   ├── api/               # APIクライアント
│   ├── utils/             # ユーティリティ関数
│   └── types/             # TypeScript型定義
└── tests/                 # テストファイル
```

### 2.2 Backend (FastAPI)
```
backend/
├── app/
│   ├── main.py            # エントリーポイント
│   ├── routers/           # エンドポイント定義
│   │   ├── auth.py
│   │   ├── stress_check.py
│   │   ├── chat.py
│   │   └── dashboard.py
│   ├── models/            # Pydanticモデル（Request/Response）
│   ├── db/                # SQLAlchemyモデル & DB接続
│   │   ├── models.py
│   │   └── database.py
│   ├── services/          # ビジネスロジック
│   │   ├── auth_service.py
│   │   ├── stress_check_service.py
│   │   ├── ai_service.py
│   │   └── analysis_service.py
│   └── utils/             # ユーティリティ
│       ├── security.py    # パスワードハッシュ、JWT
│       └── pii_filter.py  # PII除去フィルター
├── alembic/               # DBマイグレーション
└── tests/                 # テストファイル
```

## 3. 命名規則

### 3.1 データベース
- テーブル名: `snake_case`、複数形（例: `stress_checks`）
- カラム名: `snake_case`
- インデックス名: `idx_<table>_<column>`
- 外部キー: `fk_<table>_<referenced_table>`

### 3.2 API エンドポイント
- RESTful原則に従う
- リソース名は複数形（例: `/api/v1/users`）
- 動詞は使用しない（`/api/v1/getUsers` ❌）
- バージョン管理: `/api/v1/` プレフィックス

### 3.3 変数・関数名
- **TypeScript**: `camelCase`
- **Python**: `snake_case`
- **定数**: `UPPER_SNAKE_CASE`（両言語共通）

## 4. Git コミット規約

### 4.1 コミットメッセージ形式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 4.2 Type
- `feat`: 新機能追加
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードフォーマット（動作に影響なし）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルドプロセス、依存関係の変更

### 4.3 例
```
feat(auth): JWT認証機能を実装

- ログイン時にJWTトークンを発行
- トークン検証ミドルウェアを追加
- リフレッシュトークン機能は未実装（次期対応）

Closes #123
```

## 5. テスト規約

### 5.1 テストファイル命名
- **Unit Test**: `test_<module_name>.py` (Python), `<module>.test.ts` (TypeScript)
- **E2E Test**: `e2e/<feature>.spec.ts` (Playwright)

### 5.2 テストカバレッジ
- **最低限**: ビジネスロジック（サービス層）は80%以上
- **必須**: 認証、ストレスチェック計算ロジックは100%

### 5.3 テスト構造
```python
# ✅ Good
def test_calculate_stress_score_normal_case():
    """正常系: 標準的な回答でストレススコアを計算"""
    # Arrange
    answers = {f"q{i}": 3 for i in range(1, 58)}
    
    # Act
    result = calculate_stress_score(answers)
    
    # Assert
    assert result.total_score == 171
    assert result.is_high_stress is False
```

## 6. 環境変数管理

### 6.1 環境変数ファイル
- `.env.example`: テンプレート（コミット可）
- `.env`: 実際の値（`.gitignore`に追加）
- 本番環境は環境変数管理サービス（AWS Secrets Manager等）を使用

### 6.2 必須環境変数
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/stressagent
MONGODB_URL=mongodb://localhost:27017/stressagent
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 7. コードレビュー指針

### 7.1 必須チェック項目
- [ ] 型安全性（`any`使用なし）
- [ ] エラーハンドリング実装
- [ ] PIIの適切な処理
- [ ] テストコード追加
- [ ] 日本語コメント・ドキュメント

### 7.2 推奨チェック項目
- [ ] パフォーマンス考慮（N+1問題等）
- [ ] セキュリティ脆弱性
- [ ] コードの可読性
