#!/bin/bash
# Codexタスクの状態を確認するスクリプト

TASK_DIR="/Users/yu01/Desktop/StressAIAgent/.codex-tasks"

if [ ! -d "$TASK_DIR" ]; then
    echo "タスクディレクトリが存在しません"
    exit 1
fi

# 引数でタスクIDを指定、なければ最新を表示
if [ -n "$1" ]; then
    TASK_ID="$1"
else
    # 最新のタスクを取得
    LATEST=$(ls -t "$TASK_DIR"/task-*.md 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
        echo "タスクが見つかりません"
        exit 1
    fi
    TASK_ID=$(basename "$LATEST" | sed 's/task-//' | sed 's/.md//')
fi

TASK_FILE="$TASK_DIR/task-$TASK_ID.md"
OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.md"
LOG_FILE="$TASK_DIR/log-$TASK_ID.txt"
PID_FILE="$TASK_DIR/pid-$TASK_ID.txt"

echo "═══════════════════════════════════════════"
echo "📋 タスク情報: $TASK_ID"
echo "═══════════════════════════════════════════"

# プロセス状態確認
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🔄 状態: 実行中 (PID: $PID)"
    else
        echo "✅ 状態: 完了"
    fi
else
    echo "❓ 状態: 不明"
fi

echo ""

# タスク内容
if [ -f "$TASK_FILE" ]; then
    echo "📝 タスク内容:"
    echo "---"
    cat "$TASK_FILE"
    echo "---"
fi

echo ""

# 出力確認
if [ -f "$OUTPUT_FILE" ]; then
    echo "📤 Codex出力:"
    echo "---"
    cat "$OUTPUT_FILE"
    echo "---"
else
    echo "📤 出力: まだありません"
fi

echo ""

# ログ末尾
if [ -f "$LOG_FILE" ]; then
    echo "📋 ログ（末尾20行）:"
    echo "---"
    tail -20 "$LOG_FILE"
    echo "---"
fi
