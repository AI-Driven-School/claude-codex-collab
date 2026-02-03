#!/bin/bash
# Claude CodeからCodexにタスクを委譲するスクリプト

set -e

TASK_DIR="/Users/yu01/Desktop/StressAIAgent/.codex-tasks"
mkdir -p "$TASK_DIR"

TASK_ID=$(date +%Y%m%d-%H%M%S)
TASK_FILE="$TASK_DIR/task-$TASK_ID.md"
OUTPUT_FILE="$TASK_DIR/output-$TASK_ID.md"
LOG_FILE="$TASK_DIR/log-$TASK_ID.txt"

# 引数からタスク内容を取得
TASK_PROMPT="$1"

if [ -z "$TASK_PROMPT" ]; then
    echo "Usage: $0 \"タスクの説明\""
    exit 1
fi

# タスクファイル作成
cat > "$TASK_FILE" << EOF
# Codex Task: $TASK_ID

## 指示元
Claude Code

## タスク内容
$TASK_PROMPT

## 作業ルール
1. AGENTS.md のルールに従うこと
2. 完了したら TODO.md を更新すること
3. 変更内容を簡潔にまとめること

## 開始時刻
$(date '+%Y-%m-%d %H:%M:%S')
EOF

echo "📋 タスクを作成しました: $TASK_FILE"
echo "🚀 Codexを起動中..."

# Codexを実行（バックグラウンド）
cd /Users/yu01/Desktop/StressAIAgent

codex exec --full-auto \
    --cd /Users/yu01/Desktop/StressAIAgent \
    -o "$OUTPUT_FILE" \
    "$TASK_PROMPT

作業完了後、以下を実行してください：
1. TODO.md を更新（完了タスクに追加）
2. 変更内容のサマリーを出力" \
    > "$LOG_FILE" 2>&1 &

CODEX_PID=$!
echo "$CODEX_PID" > "$TASK_DIR/pid-$TASK_ID.txt"

echo ""
echo "✅ Codexがバックグラウンドで実行中 (PID: $CODEX_PID)"
echo ""
echo "📁 タスクID: $TASK_ID"
echo "📄 タスクファイル: $TASK_FILE"
echo "📝 出力ファイル: $OUTPUT_FILE"
echo "📋 ログファイル: $LOG_FILE"
echo ""
echo "進捗確認: tail -f $LOG_FILE"
echo "結果確認: cat $OUTPUT_FILE"
