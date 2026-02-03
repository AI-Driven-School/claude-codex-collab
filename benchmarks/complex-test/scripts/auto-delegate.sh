#!/bin/bash
# 自動タスク委譲スクリプト
# Claude Codeから呼び出して、タスクタイプに応じて自動実行

set -e

TASK_TYPE="$1"
TASK_ARGS="$2"
PROJECT_DIR="/Users/yu01/Desktop/StressAIAgent"
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
        TARGET="${TASK_ARGS:-backend/app/}"
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "${TARGET}のユニットテストを作成してください。pytestを使用し、モックを適切に活用してください。" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;

    "docs")
        echo "📝 Codexでドキュメント生成を実行中..."
        TARGET="${TASK_ARGS:-README.md}"
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "${TARGET}のドキュメントを生成・更新してください。" \
            2>&1 | tee "$OUTPUT_FILE"
        ;;

    "refactor")
        echo "🔧 Codexでリファクタリングを実行中..."
        TARGET="${TASK_ARGS:-backend/app/}"
        codex exec --full-auto \
            -C "$PROJECT_DIR" \
            "${TARGET}のコードを整理・リファクタリングしてください。機能は変更せず、可読性とメンテナンス性を向上させてください。" \
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
        echo "  $0 review [base-branch]     # コードレビュー"
        echo "  $0 test [target-path]       # テスト作成"
        echo "  $0 docs [target-file]       # ドキュメント生成"
        echo "  $0 refactor [target-path]   # リファクタリング"
        echo "  $0 custom \"タスク内容\"      # カスタムタスク"
        echo "  $0 background \"タスク内容\"  # バックグラウンド実行"
        exit 1
        ;;
esac

echo ""
echo "✅ 完了 - 出力: $OUTPUT_FILE"
