#!/bin/bash
# ============================================
# Claude Code + Codex 自動連携セットアップ
# ============================================
# 使用方法:
#   curl -sL https://raw.githubusercontent.com/your-repo/setup.sh | bash
#   または
#   ./setup.sh [project-dir]
# ============================================

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║  Claude Code + Codex 自動連携セットアップ  ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# プロジェクトディレクトリ
PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"
PROJECT_DIR=$(pwd)

echo -e "${YELLOW}📁 プロジェクト: ${PROJECT_DIR}${NC}"
echo ""

# 必要なコマンドの確認
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1 (未インストール)"
        return 1
    fi
}

echo "🔍 必要なコマンドを確認中..."
MISSING=0
check_command "claude" || MISSING=1
check_command "codex" || MISSING=1

if [ $MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}必要なコマンドがインストールされていません。${NC}"
    echo "以下をインストールしてください:"
    echo "  - Claude Code: npm install -g @anthropic-ai/claude-code"
    echo "  - Codex CLI: npm install -g @openai/codex"
    exit 1
fi
echo ""

# scriptsディレクトリ作成
echo "📁 ディレクトリを作成中..."
mkdir -p scripts
mkdir -p .codex-tasks
echo -e "  ${GREEN}✓${NC} scripts/"
echo -e "  ${GREEN}✓${NC} .codex-tasks/"
echo ""

# CLAUDE.md 作成
echo "📝 設定ファイルを作成中..."

cat > CLAUDE.md << 'CLAUDE_EOF'
# CLAUDE.md - Claude Code 自動設定

## プロジェクト概要

<!-- プロジェクトの説明を記載 -->

## 自動タスク委譲ルール

### Codexへの自動委譲

以下のタスクは **自動的にCodexに委譲** してください：

| キーワード | アクション |
|-----------|-----------|
| 「レビュー」「review」 | `./scripts/auto-delegate.sh review` |
| 「テスト作成」「test」 | `./scripts/auto-delegate.sh test [path]` |
| 「ドキュメント」 | `./scripts/auto-delegate.sh docs` |
| 「リファクタ」 | `./scripts/auto-delegate.sh refactor [path]` |

### サブエージェント活用

| 状況 | 起動 |
|-----|------|
| コード探索 | `Task(subagent_type="Explore")` |
| 計画立案 | `Task(subagent_type="Plan")` |
| 並列調査 | 複数Task並列起動 |

### 実装フロー（自動）

```
[依頼] → [Explore調査] → [実装] → [Codexレビュー] → [修正] → [完了]
```

## 委譲コマンド

```bash
./scripts/auto-delegate.sh review              # コードレビュー
./scripts/auto-delegate.sh test [path]         # テスト作成
./scripts/auto-delegate.sh docs                # ドキュメント生成
./scripts/auto-delegate.sh refactor [path]     # リファクタリング
./scripts/auto-delegate.sh custom "タスク"     # カスタムタスク
./scripts/auto-delegate.sh background "タスク" # バックグラウンド実行
```
CLAUDE_EOF
echo -e "  ${GREEN}✓${NC} CLAUDE.md"

# AGENTS.md 作成
cat > AGENTS.md << 'AGENTS_EOF'
# AGENTS.md - AI Agent Collaboration Guide

このファイルはClaude Code / Codex が共同作業するためのガイドです。

## プロジェクト概要

<!-- プロジェクトの説明を記載 -->

## ディレクトリ構造

```
<!-- ディレクトリ構造を記載 -->
```

## 開発ルール

### コーディング規約

- コメント: 日本語可
- 変数名・関数名: 英語

### タスク管理

作業前に `TODO.md` を確認・更新してください。

## Claude Code → Codex タスク委譲

```bash
# タスク委譲
./scripts/auto-delegate.sh review

# 状態確認
./scripts/check-codex-task.sh
```

## 推奨タスク分担

| タスク | 担当 |
|-------|------|
| 設計・計画 | Claude Code |
| 実装 | Claude Code |
| コードレビュー | Codex |
| テスト作成 | Codex |
| ドキュメント | Codex |
| デバッグ | Claude Code |

## エージェント識別子

- `@claude-code` - Claude Code
- `@codex` - Codex
- `@human` - 人間
AGENTS_EOF
echo -e "  ${GREEN}✓${NC} AGENTS.md"

# TODO.md 作成
cat > TODO.md << 'TODO_EOF'
# TODO - タスク管理

## 進行中のタスク

なし

## 未着手タスク

- [ ] タスク例 (@担当)

## 完了タスク

---

## フォーマット

```markdown
- [ ] タスク名 (@担当エージェント)
  - 詳細説明
  - 関連ファイル: `path/to/file`
```
TODO_EOF
echo -e "  ${GREEN}✓${NC} TODO.md"

# auto-delegate.sh 作成
cat > scripts/auto-delegate.sh << 'DELEGATE_EOF'
#!/bin/bash
# 自動タスク委譲スクリプト

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
        echo "🔍 Codexでコードレビューを実行中..."
        if [ -n "$TASK_ARGS" ]; then
            codex review --base "$TASK_ARGS" 2>&1 | tee "$OUTPUT_FILE"
        else
            codex review --uncommitted 2>&1 | tee "$OUTPUT_FILE"
        fi
        ;;

    "test")
        echo "🧪 Codexでテスト作成を実行中..."
        TARGET="${TASK_ARGS:-.}"
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "${TARGET}のユニットテストを作成してください。" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;

    "docs")
        echo "📝 Codexでドキュメント生成を実行中..."
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "プロジェクトのドキュメントを生成・更新してください。" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;

    "refactor")
        echo "🔧 Codexでリファクタリングを実行中..."
        TARGET="${TASK_ARGS:-.}"
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "${TARGET}のコードを整理・リファクタリングしてください。" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;

    "custom")
        echo "⚡ Codexでカスタムタスクを実行中..."
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "$TASK_ARGS" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;

    "background")
        echo "🚀 Codexをバックグラウンドで実行中..."
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "$TASK_ARGS" \
            > "$OUTPUT_FILE" 2>&1 &
        echo "タスクID: $TASK_ID"
        echo "出力ファイル: $OUTPUT_FILE"
        echo "PID: $!"
        echo "$!" > "$TASK_DIR/pid-$TASK_ID.txt"
        exit 0
        ;;

    *)
        echo "使用方法:"
        echo "  $0 review [base-branch]"
        echo "  $0 test [target-path]"
        echo "  $0 docs"
        echo "  $0 refactor [target-path]"
        echo "  $0 custom \"タスク内容\""
        echo "  $0 background \"タスク内容\""
        exit 1
        ;;
esac

echo ""
echo "✅ 完了 - 出力: $OUTPUT_FILE"
DELEGATE_EOF
chmod +x scripts/auto-delegate.sh
echo -e "  ${GREEN}✓${NC} scripts/auto-delegate.sh"

# check-codex-task.sh 作成
cat > scripts/check-codex-task.sh << 'CHECK_EOF'
#!/bin/bash
# Codexタスク状態確認スクリプト

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASK_DIR="$PROJECT_DIR/.codex-tasks"

if [ ! -d "$TASK_DIR" ]; then
    echo "タスクディレクトリが存在しません"
    exit 1
fi

if [ -n "$1" ]; then
    TASK_ID="$1"
else
    LATEST=$(ls -t "$TASK_DIR"/output-*.txt 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
        echo "タスクが見つかりません"
        exit 1
    fi
    TASK_ID=$(basename "$LATEST" | sed 's/output-//' | sed 's/.txt//')
fi

OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.txt"
PID_FILE="$TASK_DIR/pid-$TASK_ID.txt"

echo "═══════════════════════════════════════════"
echo "📋 タスク: $TASK_ID"
echo "═══════════════════════════════════════════"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🔄 状態: 実行中 (PID: $PID)"
    else
        echo "✅ 状態: 完了"
    fi
fi

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "📤 出力（末尾30行）:"
    echo "---"
    tail -30 "$OUTPUT_FILE"
fi
CHECK_EOF
chmod +x scripts/check-codex-task.sh
echo -e "  ${GREEN}✓${NC} scripts/check-codex-task.sh"

# .gitignore 追記
if [ -f .gitignore ]; then
    if ! grep -q ".codex-tasks" .gitignore; then
        echo "" >> .gitignore
        echo "# Codex tasks" >> .gitignore
        echo ".codex-tasks/" >> .gitignore
        echo -e "  ${GREEN}✓${NC} .gitignore (更新)"
    fi
else
    echo ".codex-tasks/" > .gitignore
    echo -e "  ${GREEN}✓${NC} .gitignore (作成)"
fi

echo ""
echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 使い方:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Claude Codeを起動:"
echo "   ${BLUE}claude${NC}"
echo ""
echo "2. 自動連携が有効になります:"
echo "   - 「レビューして」→ Codexが自動実行"
echo "   - 「テスト作成して」→ Codexが自動実行"
echo ""
echo "3. 手動でCodexに委譲:"
echo "   ${BLUE}./scripts/auto-delegate.sh review${NC}"
echo ""
echo "4. タスク状態確認:"
echo "   ${BLUE}./scripts/check-codex-task.sh${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
