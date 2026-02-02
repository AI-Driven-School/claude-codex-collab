#!/bin/bash
# ============================================
# Claude Code トークン95%削減テンプレート
# ============================================
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install-fullstack.sh | bash
#   curl -fsSL ... | bash -s -- my-project-name
# ============================================

set -e

VERSION="3.0.0"
REPO_RAW="https://raw.githubusercontent.com/yu010101/claude-codex-collab/main"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

print_banner() {
    echo -e "${CYAN}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│                                                         │"
    echo "│   Claude Code トークン消費 95% 削減                     │"
    echo "│                                                         │"
    echo "│   テスト・レビュー・ドキュメントを Codex に自動委譲      │"
    echo "│                                                         │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "  ${YELLOW}○${NC} $1 (未インストール)"
        return 1
    fi
}

print_banner

# プロジェクト名とディレクトリ
PROJECT_NAME="${1:-}"
if [ -n "$PROJECT_NAME" ]; then
    mkdir -p "$PROJECT_NAME"
    cd "$PROJECT_NAME"
fi
PROJECT_DIR=$(pwd)
PROJECT_NAME=${PROJECT_NAME:-$(basename "$PROJECT_DIR")}

echo -e "${CYAN}📁 プロジェクト: ${PROJECT_NAME}${NC}"
echo ""

# ===== 必要なコマンド確認 =====
echo "ツールを確認中..."
echo ""

MISSING_REQUIRED=0
MISSING_OPTIONAL=0

check_command "node" || MISSING_REQUIRED=1
check_command "npm" || MISSING_REQUIRED=1
check_command "git" || MISSING_REQUIRED=1
check_command "claude" || MISSING_OPTIONAL=1
check_command "codex" || MISSING_OPTIONAL=1

echo ""

if [ $MISSING_REQUIRED -eq 1 ]; then
    echo -e "${RED}Node.js が必要です: https://nodejs.org/${NC}"
    exit 1
fi

# オプションツールのインストール
if [ $MISSING_OPTIONAL -eq 1 ]; then
    echo -e "${YELLOW}AI ツールが見つかりません${NC}"
    read -p "自動インストール？ [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        command -v claude &> /dev/null || npm install -g @anthropic-ai/claude-code
        command -v codex &> /dev/null || npm install -g @openai/codex
        echo -e "${GREEN}✓ インストール完了${NC}"
    fi
fi

# ===== ディレクトリ構造作成 =====
echo ""
echo "セットアップ中..."
mkdir -p scripts
mkdir -p .codex-tasks
mkdir -p .claude/skills

# ===== CLAUDE.md 作成 =====
cat > CLAUDE.md << 'EOF'
# CLAUDE.md

## 自動タスク委譲

| キーワード | アクション |
|-----------|-----------|
| レビュー | `./scripts/auto-delegate.sh review` |
| テスト作成 | `./scripts/auto-delegate.sh test` |
| ドキュメント | `./scripts/auto-delegate.sh docs` |

## コマンド

| コマンド | 説明 |
|---------|------|
| `/feature <名前>` | 機能追加（設計→実装→テスト→デプロイ） |
| `/fix <内容>` | バグ修正（調査→修正→レビュー） |
| `/ui <名前>` | UIコンポーネント生成 |
| `/page <名前>` | ページUI生成 |
| `/deploy` | 本番デプロイ |
| `/review` | コードレビュー |
| `/test <path>` | テスト生成 |
EOF

# ===== AGENTS.md =====
cat > AGENTS.md << 'EOF'
# AGENTS.md

## タスク分担

| タスク | 担当 |
|-------|------|
| 設計・実装 | Claude Code |
| テスト | Codex |
| レビュー | Codex |
| ドキュメント | Codex |
EOF

# ===== カスタムスキル: ui =====
cat > .claude/skills/ui.md << 'EOF'
---
name: ui
description: UIコンポーネント生成
---

# /ui スキル

AI臭くない、プロダクション品質のUIコンポーネントを生成。

## 使用方法

```
/ui ログインフォーム
/ui ユーザーカード
/ui データテーブル
```

## 生成ルール

- Tailwind CSS 使用
- アクセシビリティ考慮
- レスポンシブ対応
- ダークモード対応
EOF

# ===== カスタムスキル: page =====
cat > .claude/skills/page.md << 'EOF'
---
name: page
description: ページ全体のUI生成
---

# /page スキル

ページ全体のレイアウトとUIを生成。

## 使用方法

```
/page ダッシュボード
/page 設定画面
/page ランディングページ
```
EOF

# ===== カスタムスキル: feature =====
cat > .claude/skills/feature.md << 'EOF'
---
name: feature
description: 機能追加ワークフロー
---

# /feature スキル

機能追加の全工程を自動実行。

## ワークフロー

1. 設計（Plan サブエージェント）
2. UI生成（/ui スキル）
3. 実装
4. テスト（Codex委譲）
5. レビュー（Codex委譲）
6. デプロイ

## 使用方法

```
/feature ユーザー認証
/feature 通知システム
/feature 検索機能
```
EOF

# ===== カスタムスキル: fix =====
cat > .claude/skills/fix.md << 'EOF'
---
name: fix
description: バグ修正ワークフロー
---

# /fix スキル

バグ修正の全工程を自動実行。

## ワークフロー

1. 調査（Explore サブエージェント）
2. 修正
3. レビュー（Codex委譲）
4. デプロイ

## 使用方法

```
/fix ログインエラー
/fix データが保存されない
/fix 画面が表示されない
```
EOF

# ===== カスタムスキル: deploy =====
cat > .claude/skills/deploy.md << 'EOF'
---
name: deploy
description: デプロイ実行
---

# /deploy スキル

本番環境にデプロイ。

## 実行コマンド

```bash
npm run build && vercel --prod
```

## プレビュー

```
/deploy preview
```
EOF

# ===== カスタムスキル: review =====
cat > .claude/skills/review.md << 'EOF'
---
name: review
description: コードレビュー
---

# /review スキル

Codexでコードレビューを実行。

## 実行コマンド

```bash
./scripts/auto-delegate.sh review
```
EOF

# ===== カスタムスキル: test =====
cat > .claude/skills/test.md << 'EOF'
---
name: test
description: テスト生成
---

# /test スキル

Codexでテストを生成。

## 使用方法

```
/test src/components/
/test lib/utils.ts
```

## 実行コマンド

```bash
./scripts/auto-delegate.sh test [path]
```
EOF

# ===== auto-delegate.sh =====
cat > scripts/auto-delegate.sh << 'SCRIPT_EOF'
#!/bin/bash
set -e

TASK_TYPE="$1"
TASK_ARGS="$2"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASK_DIR="$PROJECT_DIR/.codex-tasks"
mkdir -p "$TASK_DIR"

TASK_ID=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.txt"

cd "$PROJECT_DIR"

case "$TASK_TYPE" in
    "review")
        echo "Codex: コードレビュー..."
        if [ -n "$TASK_ARGS" ]; then
            codex review --base "$TASK_ARGS" 2>&1 | tee "$OUTPUT_FILE"
        else
            codex review --uncommitted 2>&1 | tee "$OUTPUT_FILE"
        fi
        ;;
    "test")
        echo "Codex: テスト作成..."
        TARGET="${TASK_ARGS:-.}"
        codex exec --full-auto -C "$PROJECT_DIR" \
            "${TARGET}のユニットテストを作成" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;
    "docs")
        echo "Codex: ドキュメント生成..."
        codex exec --full-auto -C "$PROJECT_DIR" \
            "ドキュメントを生成・更新" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;
    *)
        echo "使用方法:"
        echo "  $0 review [base]"
        echo "  $0 test [path]"
        echo "  $0 docs"
        exit 1
        ;;
esac
echo "完了: $OUTPUT_FILE"
SCRIPT_EOF
chmod +x scripts/auto-delegate.sh

# ===== .gitignore =====
cat > .gitignore << 'EOF'
node_modules/
.next/
.env
.env.local
.codex-tasks/
.DS_Store
EOF

# ===== 完了メッセージ =====
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}セットアップ完了${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Claude Code を起動:"
echo -e "   ${BLUE}claude${NC}"
echo ""
echo "2. コマンド:"
echo -e "   ${BLUE}/feature ユーザー認証${NC}  - 機能追加"
echo -e "   ${BLUE}/fix ログインエラー${NC}   - バグ修正"
echo -e "   ${BLUE}/ui ログインフォーム${NC}  - UI生成"
echo -e "   ${BLUE}/deploy${NC}               - デプロイ"
echo ""
