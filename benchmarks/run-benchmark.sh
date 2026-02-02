#!/bin/bash

# ベンチマーク実行スクリプト
# 使い方: ./run-benchmark.sh [claude|codex|all]

set -e

BENCHMARK_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$BENCHMARK_DIR/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

# 色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# タスク定義
TASKS=(
    "task1-todo:TODOアプリ:React + TypeScript で CRUD + localStorage の TODO アプリを実装してください。src/components/TodoApp.tsx, src/types/todo.ts, src/hooks/useTodos.ts を作成。"
    "task2-auth:認証API:FastAPI で JWT 認証 API を実装してください。POST /auth/register, /auth/login, /auth/refresh, /auth/logout。bcrypt でパスワードハッシュ化、httpOnly Cookie 使用。"
    "task3-dashboard:ダッシュボード:Next.js + Tailwind CSS でダッシュボードを実装。統計カード4つ、月別売上グラフ、注文テーブル（ページネーション付き）、レスポンシブ対応。"
)

run_claude_benchmark() {
    local task_id=$1
    local task_name=$2
    local prompt=$3
    local output_file="$RESULTS_DIR/claude_${task_id}_${TIMESTAMP}.txt"
    local time_file="$RESULTS_DIR/claude_${task_id}_${TIMESTAMP}_time.txt"

    echo -e "${GREEN}[Claude] $task_name を実行中...${NC}"

    # 時間計測
    START_TIME=$(date +%s.%N)

    # Claude Code 実行（非対話モード）
    claude --print "$prompt" > "$output_file" 2>&1 || true

    END_TIME=$(date +%s.%N)
    ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)

    echo "実行時間: ${ELAPSED}秒" > "$time_file"
    echo "出力ファイル: $output_file" >> "$time_file"

    # トークン数を概算（出力文字数 / 4）
    OUTPUT_CHARS=$(wc -c < "$output_file")
    ESTIMATED_TOKENS=$((OUTPUT_CHARS / 4))
    echo "推定出力トークン: $ESTIMATED_TOKENS" >> "$time_file"

    # コスト概算（$15/1M output tokens）
    COST=$(echo "scale=4; $ESTIMATED_TOKENS * 15 / 1000000" | bc)
    echo "推定コスト: \$$COST" >> "$time_file"

    echo -e "${GREEN}[Claude] $task_name 完了: ${ELAPSED}秒, 推定\$$COST${NC}"
    echo ""
}

run_codex_benchmark() {
    local task_id=$1
    local task_name=$2
    local prompt=$3
    local output_file="$RESULTS_DIR/codex_${task_id}_${TIMESTAMP}.txt"
    local time_file="$RESULTS_DIR/codex_${task_id}_${TIMESTAMP}_time.txt"

    echo -e "${YELLOW}[Codex] $task_name を実行中...${NC}"

    # 時間計測
    START_TIME=$(date +%s.%N)

    # Codex 実行（full-auto モード）
    codex --approval-mode full-auto "$prompt" > "$output_file" 2>&1 || true

    END_TIME=$(date +%s.%N)
    ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)

    echo "実行時間: ${ELAPSED}秒" > "$time_file"
    echo "出力ファイル: $output_file" >> "$time_file"
    echo "コスト: \$0（ChatGPT Pro に含む）" >> "$time_file"

    echo -e "${YELLOW}[Codex] $task_name 完了: ${ELAPSED}秒, コスト\$0${NC}"
    echo ""
}

# メイン
MODE=${1:-all}

echo "========================================"
echo "ベンチマーク開始: $TIMESTAMP"
echo "モード: $MODE"
echo "========================================"
echo ""

for task in "${TASKS[@]}"; do
    IFS=':' read -r task_id task_name prompt <<< "$task"

    case $MODE in
        claude)
            run_claude_benchmark "$task_id" "$task_name" "$prompt"
            ;;
        codex)
            run_codex_benchmark "$task_id" "$task_name" "$prompt"
            ;;
        all)
            run_claude_benchmark "$task_id" "$task_name" "$prompt"
            run_codex_benchmark "$task_id" "$task_name" "$prompt"
            ;;
    esac
done

echo "========================================"
echo "ベンチマーク完了"
echo "結果: $RESULTS_DIR"
echo "========================================"

# サマリー生成
SUMMARY_FILE="$RESULTS_DIR/summary_${TIMESTAMP}.md"

echo "# ベンチマーク結果 ($TIMESTAMP)" > "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"
echo "| タスク | Claude (時間) | Claude (コスト) | Codex (時間) | Codex (コスト) |" >> "$SUMMARY_FILE"
echo "|--------|--------------|----------------|-------------|---------------|" >> "$SUMMARY_FILE"

for task in "${TASKS[@]}"; do
    IFS=':' read -r task_id task_name prompt <<< "$task"

    CLAUDE_TIME_FILE="$RESULTS_DIR/claude_${task_id}_${TIMESTAMP}_time.txt"
    CODEX_TIME_FILE="$RESULTS_DIR/codex_${task_id}_${TIMESTAMP}_time.txt"

    if [ -f "$CLAUDE_TIME_FILE" ]; then
        CLAUDE_TIME=$(grep "実行時間" "$CLAUDE_TIME_FILE" | cut -d: -f2 | tr -d ' ')
        CLAUDE_COST=$(grep "推定コスト" "$CLAUDE_TIME_FILE" | cut -d: -f2 | tr -d ' ')
    else
        CLAUDE_TIME="N/A"
        CLAUDE_COST="N/A"
    fi

    if [ -f "$CODEX_TIME_FILE" ]; then
        CODEX_TIME=$(grep "実行時間" "$CODEX_TIME_FILE" | cut -d: -f2 | tr -d ' ')
        CODEX_COST=$(grep "コスト" "$CODEX_TIME_FILE" | cut -d: -f2 | tr -d ' ')
    else
        CODEX_TIME="N/A"
        CODEX_COST="N/A"
    fi

    echo "| $task_name | $CLAUDE_TIME | $CLAUDE_COST | $CODEX_TIME | $CODEX_COST |" >> "$SUMMARY_FILE"
done

echo "" >> "$SUMMARY_FILE"
echo "サマリー: $SUMMARY_FILE"
