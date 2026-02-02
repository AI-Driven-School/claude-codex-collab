#!/bin/bash
# ============================================
# Claude Code トークン95%削減（最小構成）
# ============================================
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install.sh | bash
# ============================================

set -e

VERSION="3.0.0"

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "┌───────────────────────────────────────────┐"
echo "│  Claude Code トークン消費 95% 削減        │"
echo "│  最小構成版（Claude Code + Codex のみ）   │"
echo "└───────────────────────────────────────────┘"
echo -e "${NC}"

PROJECT_DIR="${1:-.}"
if [ "$PROJECT_DIR" = "." ]; then
    PROJECT_DIR=$(pwd)
else
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    PROJECT_DIR=$(pwd)
fi

echo "セットアップ中..."

mkdir -p scripts
mkdir -p .codex-tasks
mkdir -p .claude/skills

# ===== CLAUDE.md =====
cat > CLAUDE.md << 'EOF'
# CLAUDE.md

## 自動タスク委譲

| キーワード | アクション |
|-----------|-----------|
| レビュー | `./scripts/auto-delegate.sh review` |
| テスト作成 | `./scripts/auto-delegate.sh test` |
| ドキュメント | `./scripts/auto-delegate.sh docs` |
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

echo ""
echo -e "${GREEN}セットアップ完了${NC}"
echo ""
echo "Claude Code を起動:"
echo -e "  ${BLUE}claude${NC}"
echo ""
echo "Codex委譲:"
echo -e "  ${BLUE}./scripts/auto-delegate.sh review${NC}"
echo -e "  ${BLUE}./scripts/auto-delegate.sh test${NC}"
echo ""
