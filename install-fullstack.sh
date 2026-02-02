#!/bin/bash
# ============================================
# 3AI協調開発テンプレート
# Claude Code + Codex + Gemini CLI
# ============================================

set -e

VERSION="4.0.0"

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "┌─────────────────────────────────────────────────────────┐"
echo "│                                                         │"
echo "│   3AI協調開発テンプレート                               │"
echo "│                                                         │"
echo "│   Claude Code = 設計・実装                              │"
echo "│   Codex       = テスト・レビュー                        │"
echo "│   Gemini      = 大規模解析・リサーチ                    │"
echo "│                                                         │"
echo "└─────────────────────────────────────────────────────────┘"
echo -e "${NC}"

# プロジェクト設定
PROJECT_NAME="${1:-}"
if [ -n "$PROJECT_NAME" ]; then
    mkdir -p "$PROJECT_NAME"
    cd "$PROJECT_NAME"
fi
PROJECT_DIR=$(pwd)

echo "ツールを確認中..."
echo ""

# 必須ツール確認
for cmd in node npm git; do
    if command -v "$cmd" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $cmd"
    else
        echo -e "  ${YELLOW}✗${NC} $cmd (必須)"
        exit 1
    fi
done

echo ""

# AIツール確認
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

# AIツールインストール
if [ $MISSING_AI -eq 1 ]; then
    echo -e "${YELLOW}AIツールをインストールしますか？${NC}"
    read -p "[Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        command -v claude &> /dev/null || npm install -g @anthropic-ai/claude-code
        command -v codex &> /dev/null || npm install -g @openai/codex
        command -v gemini &> /dev/null || npm install -g @google/gemini-cli
        echo -e "${GREEN}✓ インストール完了${NC}"
    fi
fi

# ディレクトリ作成
echo ""
echo "セットアップ中..."
mkdir -p scripts
mkdir -p .codex-tasks
mkdir -p .gemini-tasks
mkdir -p .claude/skills

# ===== CLAUDE.md =====
cat > CLAUDE.md << 'EOF'
# CLAUDE.md - 3AI協調開発

## タスク分担

| タスク | 担当AI | 委譲コマンド |
|-------|--------|-------------|
| 設計・複雑な実装 | Claude Code | - |
| コードレビュー | Codex | `./scripts/delegate.sh codex review` |
| テスト生成 | Codex | `./scripts/delegate.sh codex test` |
| 大規模コード解析 | Gemini | `./scripts/delegate.sh gemini analyze` |
| リサーチ | Gemini | `./scripts/delegate.sh gemini research` |
| リファクタリング | Gemini | `./scripts/delegate.sh gemini refactor` |

## 自動委譲ルール

| キーワード | 委譲先 |
|-----------|--------|
| 「レビュー」「review」 | Codex |
| 「テスト作成」「test」 | Codex |
| 「解析」「analyze」 | Gemini |
| 「リサーチ」「調査」 | Gemini |
| 「リファクタ」 | Gemini |

## コマンド

| コマンド | 説明 | 担当 |
|---------|------|------|
| `/feature` | 機能追加 | Claude + Codex |
| `/fix` | バグ修正 | Claude + Codex |
| `/ui` | UI生成 | Claude |
| `/review` | レビュー | Codex |
| `/test` | テスト生成 | Codex |
| `/analyze` | コード解析 | Gemini |
| `/research` | リサーチ | Gemini |
| `/refactor` | リファクタ | Gemini |
| `/deploy` | デプロイ | Claude |
EOF

# ===== AGENTS.md =====
cat > AGENTS.md << 'EOF'
# AGENTS.md - 3AI協調ガイド

## AI別の強み

| AI | 強み | 最適タスク |
|----|------|-----------|
| Claude Code | 推論・設計・複雑な実装 | アーキテクチャ、新機能、バグ修正 |
| Codex | 高速・自動化・構造化出力 | テスト、レビュー、ドキュメント |
| Gemini | 1Mトークン・Google検索連携 | 大規模解析、リサーチ、リファクタ |

## コスト最適化

```
Claude Code: $0.015/1K tokens（最も高価）
  → 設計・複雑な実装のみに使用

Codex: $0.01/1K tokens
  → 定型作業（テスト・レビュー）

Gemini: 無料枠あり
  → 大規模解析・リサーチを優先的に委譲
```

## 識別子

- `@claude` - Claude Code
- `@codex` - Codex
- `@gemini` - Gemini CLI
EOF

# ===== delegate.sh（統合版） =====
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
        TASK_DIR="$PROJECT_DIR/.codex-tasks"
        mkdir -p "$TASK_DIR"
        OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.txt"

        case "$TASK" in
            "review")
                echo "Codex: コードレビュー..."
                if [ -n "$ARGS" ]; then
                    codex review --base "$ARGS" 2>&1 | tee "$OUTPUT_FILE"
                else
                    codex review --uncommitted 2>&1 | tee "$OUTPUT_FILE"
                fi
                ;;
            "test")
                echo "Codex: テスト生成..."
                TARGET="${ARGS:-.}"
                codex exec --full-auto -C "$PROJECT_DIR" \
                    "${TARGET}のユニットテストを作成" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            "docs")
                echo "Codex: ドキュメント生成..."
                codex exec --full-auto -C "$PROJECT_DIR" \
                    "ドキュメントを生成・更新" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            *)
                echo "Codexタスク: review, test, docs"
                exit 1
                ;;
        esac
        ;;

    "gemini")
        TASK_DIR="$PROJECT_DIR/.gemini-tasks"
        mkdir -p "$TASK_DIR"
        OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.txt"

        case "$TASK" in
            "analyze")
                echo "Gemini: コード解析..."
                TARGET="${ARGS:-.}"
                gemini -p "このコードベースを解析して構造と改善点を報告: $TARGET" \
                    2>&1 | tee "$OUTPUT_FILE"
                ;;
            "research")
                echo "Gemini: リサーチ..."
                gemini -p "$ARGS" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            "refactor")
                echo "Gemini: リファクタリング提案..."
                TARGET="${ARGS:-.}"
                gemini -p "このコードのリファクタリング案を提案: $TARGET" \
                    2>&1 | tee "$OUTPUT_FILE"
                ;;
            "explain")
                echo "Gemini: コード説明..."
                TARGET="${ARGS:-.}"
                gemini -p "このコードを詳細に説明: $TARGET" 2>&1 | tee "$OUTPUT_FILE"
                ;;
            *)
                echo "Geminiタスク: analyze, research, refactor, explain"
                exit 1
                ;;
        esac
        ;;

    *)
        echo "使用方法:"
        echo "  $0 codex review [base]"
        echo "  $0 codex test [path]"
        echo "  $0 codex docs"
        echo ""
        echo "  $0 gemini analyze [path]"
        echo "  $0 gemini research \"質問\""
        echo "  $0 gemini refactor [path]"
        echo "  $0 gemini explain [path]"
        exit 1
        ;;
esac

echo "完了: $OUTPUT_FILE"
SCRIPT_EOF
chmod +x scripts/delegate.sh

# ===== スキル: analyze =====
cat > .claude/skills/analyze.md << 'EOF'
---
name: analyze
description: 大規模コード解析（Gemini委譲）
---

# /analyze スキル

Geminiの1Mトークンコンテキストを活用した大規模コード解析。

## 使用方法

```
/analyze              # プロジェクト全体
/analyze src/         # 特定ディレクトリ
/analyze --deps       # 依存関係分析
```

## 実行コマンド

```bash
./scripts/delegate.sh gemini analyze [path]
```

## 出力

- コード構造の概要
- 依存関係グラフ
- 改善提案
- 技術的負債の特定
EOF

# ===== スキル: research =====
cat > .claude/skills/research.md << 'EOF'
---
name: research
description: リサーチ（Gemini委譲）
---

# /research スキル

GeminiのGoogle検索連携を活用したリサーチ。

## 使用方法

```
/research "Next.js 15の新機能"
/research "Supabase vs Firebase 比較"
/research "TypeScript 5.0 移行ガイド"
```

## 実行コマンド

```bash
./scripts/delegate.sh gemini research "質問"
```
EOF

# ===== スキル: refactor =====
cat > .claude/skills/refactor.md << 'EOF'
---
name: refactor
description: リファクタリング提案（Gemini委譲）
---

# /refactor スキル

Geminiの大規模コンテキストを活用したリファクタリング提案。

## 使用方法

```
/refactor src/components/
/refactor lib/api/
/refactor --pattern "Repository Pattern適用"
```

## 実行コマンド

```bash
./scripts/delegate.sh gemini refactor [path]
```

## 出力

- リファクタリング対象の特定
- 具体的な改善案
- Before/After コード例
EOF

# ===== 既存スキル更新 =====
cat > .claude/skills/ui.md << 'EOF'
---
name: ui
description: UIコンポーネント生成
---

# /ui スキル

AI臭くない、プロダクション品質のUIコンポーネントを生成。

```
/ui ログインフォーム
/ui ユーザーカード
```
EOF

cat > .claude/skills/feature.md << 'EOF'
---
name: feature
description: 機能追加ワークフロー
---

# /feature スキル

## ワークフロー

1. 設計（Claude）
2. UI生成（Claude）
3. 実装（Claude）
4. テスト（Codex委譲）
5. レビュー（Codex委譲）
6. デプロイ

```
/feature ユーザー認証
```
EOF

cat > .claude/skills/fix.md << 'EOF'
---
name: fix
description: バグ修正ワークフロー
---

# /fix スキル

## ワークフロー

1. 解析（Gemini委譲 - 大規模コードベースの場合）
2. 修正（Claude）
3. レビュー（Codex委譲）

```
/fix ログインエラー
```
EOF

cat > .claude/skills/review.md << 'EOF'
---
name: review
description: コードレビュー（Codex委譲）
---

# /review スキル

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

```
/test src/components/
```

```bash
./scripts/delegate.sh codex test [path]
```
EOF

cat > .claude/skills/deploy.md << 'EOF'
---
name: deploy
description: デプロイ
---

# /deploy スキル

```bash
npm run build && vercel --prod
```
EOF

# ===== .gitignore =====
cat > .gitignore << 'EOF'
node_modules/
.next/
.env
.env.local
.codex-tasks/
.gemini-tasks/
.DS_Store
EOF

# ===== 完了メッセージ =====
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}3AI協調開発テンプレート セットアップ完了${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Claude Code を起動:"
echo -e "  ${BLUE}claude${NC}"
echo ""
echo "コマンド:"
echo -e "  ${BLUE}/feature${NC}   機能追加      → Claude + Codex"
echo -e "  ${BLUE}/review${NC}    レビュー      → Codex"
echo -e "  ${BLUE}/test${NC}      テスト生成    → Codex"
echo -e "  ${BLUE}/analyze${NC}   コード解析    → Gemini"
echo -e "  ${BLUE}/research${NC}  リサーチ      → Gemini"
echo -e "  ${BLUE}/refactor${NC}  リファクタ    → Gemini"
echo ""
