#!/bin/bash
# ============================================
# 3AI協調開発テンプレート v5.0
# 要件定義から本番まで承認フロー付き
# ============================================

set -e

VERSION="5.0.0"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "┌─────────────────────────────────────────────────────────┐"
echo "│                                                         │"
echo "│   3AI協調開発テンプレート v5.0                          │"
echo "│                                                         │"
echo "│   要件定義 → 設計 → 実装 → テスト → デプロイ           │"
echo "│   承認フロー付きで完全自動化                            │"
echo "│                                                         │"
echo "└─────────────────────────────────────────────────────────┘"
echo -e "${NC}"

PROJECT_NAME="${1:-}"
if [ -n "$PROJECT_NAME" ]; then
    mkdir -p "$PROJECT_NAME"
    cd "$PROJECT_NAME"
fi
PROJECT_DIR=$(pwd)

echo "ツールを確認中..."
echo ""

for cmd in node npm git; do
    if command -v "$cmd" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $cmd"
    else
        echo -e "  ${YELLOW}✗${NC} $cmd (必須)"
        exit 1
    fi
done

echo ""

MISSING_AI=0
for cmd in claude codex gemini; do
    if command -v "$cmd" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $cmd"
    else
        echo -e "  ${YELLOW}○${NC} $cmd"
        MISSING_AI=1
    fi
done

echo ""

if [ $MISSING_AI -eq 1 ]; then
    read -p "AIツールをインストール？ [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        command -v claude &> /dev/null || npm install -g @anthropic-ai/claude-code
        command -v codex &> /dev/null || npm install -g @openai/codex
        command -v gemini &> /dev/null || npm install -g @google/gemini-cli
        echo -e "${GREEN}✓ インストール完了${NC}"
    fi
fi

echo ""
echo "セットアップ中..."

# ディレクトリ構造
mkdir -p scripts
mkdir -p .claude/skills
mkdir -p .tasks/{codex,gemini}
mkdir -p docs/{requirements,specs,api,decisions,reviews}
mkdir -p mockups

# ===== CLAUDE.md =====
cat > CLAUDE.md << 'EOF'
# CLAUDE.md - 3AI協調開発 v5.0

## 開発フロー

```
/project <機能名>
    ↓
[1] 要件定義 → 承認待ち
[2] 画面設計 → 承認待ち
[3] API設計 → 承認待ち
[4] DB設計 → 承認待ち
[5] 実装 → 自動
[6] テスト → 自動（Codex）
[7] レビュー → 自動（Codex）
[8] デプロイ → 承認待ち
```

## コマンド一覧

### プロジェクト管理
| コマンド | 説明 |
|---------|------|
| `/project <名前>` | 承認フロー付き完全ワークフロー |
| `/status` | 進行中プロジェクトの状態確認 |
| `/approve` | 現在のフェーズを承認 |
| `/reject <理由>` | 現在のフェーズを却下・再生成 |

### 個別コマンド（単体実行用）
| コマンド | 説明 | 出力 |
|---------|------|------|
| `/requirements <機能>` | 要件定義 | docs/requirements/*.md |
| `/spec <画面>` | 画面設計書 | docs/specs/*.md |
| `/api <エンドポイント>` | API設計 | docs/api/*.yaml |
| `/schema <テーブル>` | DB設計 | migrations/*.sql |
| `/mockup <画面>` | モックアップ | mockups/*.png |
| `/implement` | 実装（設計書から） | src/ |
| `/test` | テスト生成 | tests/ |
| `/review` | コードレビュー | docs/reviews/*.md |
| `/deploy` | デプロイ | - |

### AI委譲
| コマンド | 担当AI |
|---------|--------|
| `/analyze` | Gemini（大規模解析） |
| `/research <質問>` | Gemini（リサーチ） |
| `/refactor <path>` | Gemini（リファクタ） |

## 自動委譲ルール

| キーワード | 委譲先 |
|-----------|--------|
| テスト作成 | Codex |
| レビュー | Codex |
| 解析・リサーチ | Gemini |
| リファクタ | Gemini |

## 成果物構造

```
docs/
├── requirements/     # 要件定義
├── specs/            # 画面設計
├── api/              # API設計（OpenAPI）
├── decisions/        # 設計判断の記録
└── reviews/          # レビュー記録
mockups/              # 画面モックアップ
migrations/           # DBマイグレーション
```
EOF

# ===== AGENTS.md =====
cat > AGENTS.md << 'EOF'
# AGENTS.md - 3AI協調ガイド

## 役割分担

| AI | 担当フェーズ |
|----|-------------|
| Claude Code | 要件定義、設計、実装、デプロイ判断 |
| Codex | テスト生成、コードレビュー |
| Gemini | 大規模解析、リサーチ、リファクタ |

## 承認フロー

人間が判断すべきポイント:
1. 要件定義の妥当性
2. 画面設計の承認
3. API設計の承認
4. DB設計の承認
5. デプロイの最終判断

AIに任せてよいポイント:
- 実装（設計承認後）
- テスト生成
- コードレビュー
EOF

# ===== スキル: project =====
cat > .claude/skills/project.md << 'EOF'
---
name: project
description: 承認フロー付き完全開発ワークフロー
---

# /project スキル

要件定義から本番デプロイまで、承認フロー付きで実行。

## 使用方法

```
/project ユーザー認証
/project 商品検索機能
/project 通知システム
```

## ワークフロー

### Phase 1: 要件定義
```
入力: 機能名
出力: docs/requirements/{機能名}.md
内容:
  - ユーザーストーリー
  - 受入条件
  - 非機能要件
  - 制約事項
→ 承認待ち
```

### Phase 2: 画面設計
```
入力: 要件定義
出力:
  - docs/specs/{画面名}.md
  - mockups/{画面名}.png
内容:
  - ワイヤーフレーム
  - コンポーネント一覧
  - 状態遷移
→ 承認待ち
```

### Phase 3: API設計
```
入力: 要件 + 画面設計
出力: docs/api/{機能名}.yaml
内容:
  - OpenAPI 3.0形式
  - エンドポイント一覧
  - リクエスト/レスポンス定義
  - エラーハンドリング
→ 承認待ち
```

### Phase 4: DB設計
```
入力: 要件 + API設計
出力: migrations/{timestamp}_{機能名}.sql
内容:
  - テーブル定義
  - インデックス
  - 制約
→ 承認待ち
```

### Phase 5: 実装
```
入力: 全設計書
出力: src/
担当: Claude Code
→ 自動実行
```

### Phase 6: テスト
```
入力: 実装コード + 受入条件
出力: tests/
担当: Codex
→ 自動実行
```

### Phase 7: レビュー
```
入力: 実装 + テスト
出力: docs/reviews/{機能名}.md
担当: Codex
→ 自動実行
```

### Phase 8: デプロイ
```
入力: レビュー結果
出力: 本番URL
→ 承認待ち
```

## 承認コマンド

```
/approve          # 現在フェーズを承認、次へ進む
/reject 理由      # 却下して再生成
/skip             # フェーズをスキップ
/status           # 現在の進捗確認
```

## 中断・再開

```
/project --resume  # 中断したプロジェクトを再開
/project --list    # 進行中プロジェクト一覧
```
EOF

# ===== スキル: requirements =====
cat > .claude/skills/requirements.md << 'EOF'
---
name: requirements
description: 要件定義書を生成
---

# /requirements スキル

ユーザーストーリー形式の要件定義書を生成。

## 使用方法

```
/requirements ユーザー認証
/requirements "メールでパスワードリセット"
```

## 出力形式

```markdown
# 要件定義: {機能名}

## ユーザーストーリー

AS A {ユーザー種別}
I WANT TO {やりたいこと}
SO THAT {得られる価値}

## 受入条件

- [ ] 条件1
- [ ] 条件2
- [ ] 条件3

## 非機能要件

- パフォーマンス:
- セキュリティ:
- 可用性:

## 制約事項

- 技術的制約:
- ビジネス制約:

## 関連機能

- 依存する機能:
- 影響を受ける機能:
```

## 出力先

`docs/requirements/{機能名}.md`
EOF

# ===== スキル: spec =====
cat > .claude/skills/spec.md << 'EOF'
---
name: spec
description: 画面設計書を生成
---

# /spec スキル

画面設計書とモックアップを生成。

## 使用方法

```
/spec ログイン画面
/spec ダッシュボード
```

## 出力形式

```markdown
# 画面設計: {画面名}

## 概要

{画面の目的と役割}

## モックアップ

![モックアップ](../mockups/{画面名}.png)

## コンポーネント一覧

| コンポーネント | 種類 | 説明 |
|--------------|------|------|
| ... | ... | ... |

## 状態

| 状態名 | トリガー | 表示内容 |
|-------|---------|---------|
| 初期表示 | ページロード | ... |
| ローディング | API呼び出し中 | ... |
| エラー | API失敗 | ... |
| 成功 | API成功 | ... |

## バリデーション

| フィールド | ルール | エラーメッセージ |
|-----------|-------|----------------|
| ... | ... | ... |

## アクセシビリティ

- キーボード操作:
- スクリーンリーダー:
- コントラスト比:
```

## 出力先

- `docs/specs/{画面名}.md`
- `mockups/{画面名}.png`
EOF

# ===== スキル: api =====
cat > .claude/skills/api.md << 'EOF'
---
name: api
description: API設計書（OpenAPI）を生成
---

# /api スキル

OpenAPI 3.0形式のAPI設計書を生成。

## 使用方法

```
/api 認証API
/api ユーザーAPI
```

## 出力形式

```yaml
openapi: 3.0.0
info:
  title: {API名}
  version: 1.0.0

paths:
  /api/v1/{リソース}:
    get:
      summary: 一覧取得
      responses:
        '200':
          description: 成功
    post:
      summary: 新規作成
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/{リソース}'

components:
  schemas:
    {リソース}:
      type: object
      properties:
        id:
          type: string
        ...
```

## 出力先

`docs/api/{API名}.yaml`
EOF

# ===== スキル: schema =====
cat > .claude/skills/schema.md << 'EOF'
---
name: schema
description: DB設計（マイグレーション）を生成
---

# /schema スキル

SQLマイグレーションファイルを生成。

## 使用方法

```
/schema users
/schema products
```

## 出力形式

```sql
-- Migration: {テーブル名}
-- Created: {timestamp}

CREATE TABLE {テーブル名} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- カラム定義
);

-- インデックス
CREATE INDEX idx_{テーブル名}_{カラム} ON {テーブル名}({カラム});

-- コメント
COMMENT ON TABLE {テーブル名} IS '{説明}';
```

## 出力先

`migrations/{timestamp}_{テーブル名}.sql`
EOF

# ===== スキル: mockup（更新） =====
cat > .claude/skills/mockup.md << 'EOF'
---
name: mockup
description: 画面モックアップを生成してPNG化
---

# /mockup スキル

画面モックアップをHTML/Tailwindで生成し、PNG画像化。

## 使用方法

```
/mockup ログイン画面
/mockup ダッシュボード --device desktop
```

## オプション

- `--device`: iphone, ipad, desktop
- `--dark`: ダークモード版も生成
- `--implement`: そのまま実装に進む

## 実装連携

```
/mockup ログイン画面 --implement

→ モックアップ生成
→ 「この設計で実装しますか？」
→ Y → モックアップのHTMLをReactコンポーネント化
```

## 出力先

`mockups/{画面名}.png`
EOF

# ===== スキル: implement =====
cat > .claude/skills/implement.md << 'EOF'
---
name: implement
description: 設計書から実装を生成
---

# /implement スキル

承認済み設計書から実装コードを生成。

## 使用方法

```
/implement               # 全設計書から実装
/implement auth          # 特定機能のみ
```

## 前提条件

以下が承認済みであること:
- docs/requirements/{機能名}.md
- docs/specs/{画面名}.md
- docs/api/{API名}.yaml
- migrations/{テーブル名}.sql

## 生成物

```
src/
├── app/
│   └── {機能名}/
│       └── page.tsx
├── components/
│   └── {機能名}/
│       └── *.tsx
├── lib/
│   └── api/
│       └── {機能名}.ts
└── types/
    └── {機能名}.ts
```
EOF

# ===== スキル: その他（既存更新） =====
cat > .claude/skills/review.md << 'EOF'
---
name: review
description: コードレビュー（Codex委譲）
---

# /review スキル

Codexでコードレビューを実行し、結果をドキュメント化。

## 出力先

`docs/reviews/{日付}_{機能名}.md`

## 実行

```bash
./scripts/delegate.sh codex review
```
EOF

cat > .claude/skills/test.md << 'EOF'
---
name: test
description: テスト生成（Codex委譲）
---

# /test スキル

受入条件に基づいてテストを生成。

## 使用方法

```
/test                    # 全テスト
/test auth               # 特定機能
```

## 実行

```bash
./scripts/delegate.sh codex test
```
EOF

cat > .claude/skills/analyze.md << 'EOF'
---
name: analyze
description: 大規模コード解析（Gemini委譲）
---

# /analyze スキル

Geminiの1Mトークンコンテキストで大規模解析。

```
/analyze
/analyze src/
```
EOF

cat > .claude/skills/research.md << 'EOF'
---
name: research
description: 技術リサーチ（Gemini委譲）
---

# /research スキル

Geminiで技術リサーチ。

```
/research "Next.js 15 App Router"
/research "認証ベストプラクティス 2025"
```
EOF

cat > .claude/skills/refactor.md << 'EOF'
---
name: refactor
description: リファクタリング提案（Gemini委譲）
---

# /refactor スキル

Geminiでリファクタリング提案。

```
/refactor src/lib/
```
EOF

cat > .claude/skills/deploy.md << 'EOF'
---
name: deploy
description: デプロイ
---

# /deploy スキル

承認後にデプロイを実行。

```
/deploy              # 本番
/deploy preview      # プレビュー
```
EOF

# ===== delegate.sh =====
cat > scripts/delegate.sh << 'SCRIPT_EOF'
#!/bin/bash
set -e

AI="$1"
TASK="$2"
ARGS="$3"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASK_ID=$(date +%Y%m%d-%H%M%S)

cd "$PROJECT_DIR"

case "$AI" in
    "codex")
        TASK_DIR="$PROJECT_DIR/.tasks/codex"
        mkdir -p "$TASK_DIR"
        OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.txt"

        case "$TASK" in
            "review")
                echo "Codex: コードレビュー..."
                codex review --uncommitted 2>&1 | tee "$OUTPUT_FILE"

                # レビュー結果をドキュメント化
                REVIEW_FILE="$PROJECT_DIR/docs/reviews/$(date +%Y%m%d)-review.md"
                echo "# コードレビュー $(date +%Y-%m-%d)" > "$REVIEW_FILE"
                echo "" >> "$REVIEW_FILE"
                cat "$OUTPUT_FILE" >> "$REVIEW_FILE"
                echo "→ $REVIEW_FILE"
                ;;
            "test")
                echo "Codex: テスト生成..."
                TARGET="${ARGS:-.}"
                codex exec --full-auto -C "$PROJECT_DIR" \
                    "${TARGET}のユニットテストを作成。受入条件に基づく。" \
                    2>&1 | tee "$OUTPUT_FILE"
                ;;
            *)
                echo "Codexタスク: review, test"
                exit 1
                ;;
        esac
        ;;

    "gemini")
        TASK_DIR="$PROJECT_DIR/.tasks/gemini"
        mkdir -p "$TASK_DIR"
        OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.txt"

        case "$TASK" in
            "analyze")
                echo "Gemini: コード解析..."
                gemini -p "このコードベースを解析: ${ARGS:-.}" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            "research")
                echo "Gemini: リサーチ..."
                gemini -p "$ARGS" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            "refactor")
                echo "Gemini: リファクタリング提案..."
                gemini -p "リファクタリング提案: ${ARGS:-.}" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            *)
                echo "Geminiタスク: analyze, research, refactor"
                exit 1
                ;;
        esac
        ;;

    *)
        echo "使用方法:"
        echo "  $0 codex review"
        echo "  $0 codex test [path]"
        echo "  $0 gemini analyze [path]"
        echo "  $0 gemini research \"質問\""
        echo "  $0 gemini refactor [path]"
        exit 1
        ;;
esac
SCRIPT_EOF
chmod +x scripts/delegate.sh

# ===== .gitignore =====
cat > .gitignore << 'EOF'
node_modules/
.next/
.env
.env.local
.tasks/
.DS_Store
EOF

# ===== 完了メッセージ =====
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}セットアップ完了 v5.0${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}完全ワークフロー:${NC}"
echo -e "  ${BLUE}/project ユーザー認証${NC}"
echo ""
echo -e "${CYAN}個別コマンド:${NC}"
echo -e "  ${BLUE}/requirements${NC}  要件定義"
echo -e "  ${BLUE}/spec${NC}          画面設計"
echo -e "  ${BLUE}/api${NC}           API設計"
echo -e "  ${BLUE}/schema${NC}        DB設計"
echo -e "  ${BLUE}/mockup${NC}        モックアップ"
echo -e "  ${BLUE}/implement${NC}     実装"
echo -e "  ${BLUE}/test${NC}          テスト生成"
echo -e "  ${BLUE}/review${NC}        レビュー"
echo -e "  ${BLUE}/deploy${NC}        デプロイ"
echo ""
echo -e "${CYAN}成果物:${NC}"
echo "  docs/requirements/  要件定義"
echo "  docs/specs/         画面設計"
echo "  docs/api/           API設計"
echo "  docs/reviews/       レビュー記録"
echo "  mockups/            モックアップ"
echo "  migrations/         DBマイグレーション"
echo ""
