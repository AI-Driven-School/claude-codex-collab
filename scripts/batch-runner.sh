#!/usr/bin/env bash
# batch-runner.sh - Parallel batch runner for Claude Code tasks
# Runs up to 100 independent tasks with concurrency control.
# Bash 3.2+ compatible.
set -euo pipefail

BATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$BATCH_DIR/.." && pwd)"

# Load libraries
source "$BATCH_DIR/lib/semaphore.sh"
source "$BATCH_DIR/lib/tui.sh"

# ── Defaults ──────────────────────────────────────────────────────
JOBS=""
TIMEOUT=300
MODEL="sonnet"
MAX_TURNS=15
OUTPUT_DIR=""
GENERATE_PROMPT=""
DRY_RUN=false
RETRY_COUNT=1
TASK_FILE=""

# ── Child PID tracking ───────────────────────────────────────────
_CHILD_PIDS_FILE=""
_PROGRESS_PID=""

_pids_init() {
    _CHILD_PIDS_FILE=$(mktemp /tmp/aiki-batch-pids.XXXXXX)
}

_pids_add() {
    echo "$1" >> "$_CHILD_PIDS_FILE"
}

# Kill tracked child PIDs individually (no kill 0)
_pids_kill_all() {
    [ -z "$_CHILD_PIDS_FILE" ] && return 0
    [ ! -f "$_CHILD_PIDS_FILE" ] && return 0
    while IFS= read -r pid; do
        [ -z "$pid" ] && continue
        # Kill child's descendants first (timeout spawns sub-processes)
        pkill -P "$pid" 2>/dev/null || true
        kill "$pid" 2>/dev/null || true
    done < "$_CHILD_PIDS_FILE"
}

_pids_cleanup() {
    [ -n "$_CHILD_PIDS_FILE" ] && rm -f "$_CHILD_PIDS_FILE" 2>/dev/null || true
}

# ── Counters (shared via files for subshell safety) ──────────────
_COUNTER_DIR=""
_LOCK_STALE_SECONDS=5

_counter_init() {
    _COUNTER_DIR=$(mktemp -d /tmp/aiki-batch-counters.XXXXXX)
    echo "0" > "$_COUNTER_DIR/done"
    echo "0" > "$_COUNTER_DIR/fail"
    echo "0" > "$_COUNTER_DIR/running"
}

# Acquire mkdir-based lock with stale detection
_lock_acquire() {
    local lock="$1"
    local attempts=0
    while ! mkdir "$lock" 2>/dev/null; do
        attempts=$((attempts + 1))
        # After ~5 seconds (100 * 0.05s), treat as stale and force-remove
        if [ "$attempts" -ge 100 ]; then
            rmdir "$lock" 2>/dev/null || rm -rf "$lock" 2>/dev/null || true
            attempts=0
        fi
        sleep 0.05
    done
}

_counter_inc() {
    local name="$1"
    local lock="$_COUNTER_DIR/${name}.lock"
    (
        _lock_acquire "$lock"
        local val
        val=$(cat "$_COUNTER_DIR/$name")
        echo $((val + 1)) > "$_COUNTER_DIR/$name"
        rmdir "$lock"
    )
}

_counter_dec() {
    local name="$1"
    local lock="$_COUNTER_DIR/${name}.lock"
    (
        _lock_acquire "$lock"
        local val
        val=$(cat "$_COUNTER_DIR/$name")
        echo $((val - 1)) > "$_COUNTER_DIR/$name"
        rmdir "$lock"
    )
}

_counter_get() {
    cat "$_COUNTER_DIR/$1" 2>/dev/null || echo "0"
}

_counter_cleanup() {
    [ -n "$_COUNTER_DIR" ] && rm -rf "$_COUNTER_DIR" 2>/dev/null || true
}

# ── Usage ─────────────────────────────────────────────────────────
show_batch_help() {
    cat << 'EOF'
aiki batch - Parallel batch runner for Claude Code

Usage:
  aiki batch <tasks.jsonl> [options]
  aiki batch --generate "<prompt>" [options]

Options:
  --jobs N        Max parallel jobs (default: auto based on RAM)
  --timeout S     Per-task timeout in seconds (default: 300)
  --model M       Default model (default: sonnet)
  --max-turns N   Max turns per task (default: 15)
  --output-dir D  Output directory (default: .batch-results/TIMESTAMP)
  --generate P    Generate task file from prompt, then run
  --dry-run       Show plan without executing
  --retry N       Retry count for failed tasks (default: 1)
  --help          Show this help

Task file format (JSONL):
  {"id":"landing","prompt":"Create a landing page...","model":"sonnet"}

Examples:
  aiki batch tasks.jsonl --jobs 8 --timeout 300
  aiki batch --generate "EC site: top, products, cart, checkout" --jobs 4
  aiki batch tasks.jsonl --dry-run
EOF
}

# ── RAM detection ─────────────────────────────────────────────────
detect_max_jobs() {
    local mem_bytes=0
    if command -v sysctl >/dev/null 2>&1; then
        # macOS
        mem_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
    elif [ -f /proc/meminfo ]; then
        # Linux
        local mem_kb
        mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        mem_bytes=$((mem_kb * 1024))
    fi

    if [ "$mem_bytes" -gt 0 ]; then
        # 1.5GB per job, leave 4GB for OS
        local available=$(( (mem_bytes - 4294967296) ))
        [ "$available" -lt 1610612736 ] && available=1610612736
        local max_jobs=$(( available / 1610612736 ))
        [ "$max_jobs" -lt 1 ] && max_jobs=1
        [ "$max_jobs" -gt 20 ] && max_jobs=20
        echo "$max_jobs"
    else
        echo "4"
    fi
}

# ── Numeric validation ───────────────────────────────────────────
_require_positive_int() {
    local flag="$1"
    local value="$2"
    case "$value" in
        ''|*[!0-9]*)
            echo "${flag} requires a positive integer, got: ${value}" >&2
            exit 1
            ;;
    esac
    if [ "$value" -le 0 ]; then
        echo "${flag} must be greater than 0, got: ${value}" >&2
        exit 1
    fi
}

# ── Argument parsing ──────────────────────────────────────────────
parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --jobs)
                JOBS="${2:?--jobs requires a number}"
                _require_positive_int "--jobs" "$JOBS"
                shift 2
                ;;
            --timeout)
                TIMEOUT="${2:?--timeout requires seconds}"
                _require_positive_int "--timeout" "$TIMEOUT"
                shift 2
                ;;
            --model)
                MODEL="${2:?--model requires a model name}"
                shift 2
                ;;
            --max-turns)
                MAX_TURNS="${2:?--max-turns requires a number}"
                _require_positive_int "--max-turns" "$MAX_TURNS"
                shift 2
                ;;
            --output-dir)
                OUTPUT_DIR="${2:?--output-dir requires a path}"
                shift 2
                ;;
            --generate)
                GENERATE_PROMPT="${2:?--generate requires a prompt}"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --retry)
                RETRY_COUNT="${2:?--retry requires a number}"
                _require_positive_int "--retry" "$RETRY_COUNT"
                shift 2
                ;;
            --help|-h)
                show_batch_help
                exit 0
                ;;
            -*)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
            *)
                if [ -z "$TASK_FILE" ]; then
                    TASK_FILE="$1"
                fi
                shift
                ;;
        esac
    done
}

# ── Generate mode ─────────────────────────────────────────────────
# Strip markdown fences from Claude output (```json ... ```)
_strip_markdown_fences() {
    sed -e '/^```/d' -e 's/^```json$//' -e 's/^```jsonl$//'
}

generate_tasks() {
    local prompt="$1"
    local outfile="$2"
    local raw_file="${outfile}.raw"

    tui_info "Generating task file from prompt..."
    tui_spinner "Claude is generating tasks..."

    claude -p \
        --model "$MODEL" \
        --output-format json \
        --max-turns 3 \
        "Generate a JSONL task file. Each line is a valid JSON object with fields: id (kebab-case), prompt (detailed implementation instructions for Next.js App Router + Tailwind + TypeScript), model (always \"sonnet\").
Output ONLY the JSONL lines, no markdown fences, no explanations.
Feature list: ${prompt}" \
        2>/dev/null | jq -r '.result // empty' > "$raw_file" || true

    tui_spinner_stop "Tasks generated"

    if [ ! -s "$raw_file" ]; then
        tui_error "Failed to generate task file"
        rm -f "$raw_file"
        exit 1
    fi

    # Strip markdown fences and keep only valid JSON lines
    _strip_markdown_fences < "$raw_file" | while IFS= read -r line; do
        [ -z "$line" ] && continue
        # Validate each line is valid JSON
        echo "$line" | jq -e '.' >/dev/null 2>&1 && echo "$line"
    done > "$outfile"
    rm -f "$raw_file"

    if [ ! -s "$outfile" ]; then
        tui_error "No valid JSONL tasks generated"
        exit 1
    fi

    local count
    count=$(wc -l < "$outfile" | tr -d ' ')
    tui_success "Generated ${count} tasks -> ${outfile}"
}

# ── Run single task ───────────────────────────────────────────────
# Each task writes result + progress to its own dir (race-free)
run_task() {
    local task_json="$1"
    local task_dir="$2"
    local task_id="$3"
    local task_model="$4"
    local task_prompt="$5"
    local task_num="$6"
    local total="$7"

    local start_time
    start_time=$(date +%s)

    mkdir -p "$task_dir"

    _counter_inc running

    local exit_code=0
    NODE_OPTIONS="--max-old-space-size=1536" \
    timeout "$TIMEOUT" claude -p \
        --model "$task_model" \
        --output-format json \
        --max-turns "$MAX_TURNS" \
        --no-session-persistence \
        --dangerously-skip-permissions \
        --allowedTools "Read" "Edit" "Write" "Bash(npm *)" "Bash(npx *)" "Glob" "Grep" \
        --append-system-prompt "Output all files to ${task_dir}. Use TypeScript + Tailwind. Code only, no explanations." \
        "$task_prompt" \
        > "$task_dir/output.json" 2>"$task_dir/error.log" || exit_code=$?

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    _counter_dec running

    local status="success"
    if [ "$exit_code" -eq 124 ]; then
        status="timeout"
    elif [ "$exit_code" -ne 0 ]; then
        status="error"
    fi

    # Write result to per-task file (race-free)
    printf '{"id":"%s","status":"%s","exit_code":%d,"duration":%d,"model":"%s"}\n' \
        "$task_id" "$status" "$exit_code" "$duration" "$task_model" \
        > "$task_dir/result.json"

    # Write progress to per-task file (race-free)
    if [ "$status" = "success" ]; then
        _counter_inc done
        printf '%s ✓ %s (%ds, %s)\n' "$(date '+%H:%M:%S')" "$task_id" "$duration" "$task_model" \
            > "$task_dir/progress.txt"
    else
        _counter_inc fail
        printf '%s ✗ %s (%s, %ds)\n' "$(date '+%H:%M:%S')" "$task_id" "$status" "$duration" \
            > "$task_dir/progress.txt"
    fi

    sem_release
}

# ── Merge per-task results ────────────────────────────────────────
merge_results() {
    local output_dir="$1"
    : > "$output_dir/results.jsonl"
    : > "$output_dir/progress.log"
    local task_dir
    for task_dir in "$output_dir"/task-*/; do
        [ -d "$task_dir" ] || continue
        [ -f "$task_dir/result.json" ] && cat "$task_dir/result.json" >> "$output_dir/results.jsonl"
        [ -f "$task_dir/progress.txt" ] && cat "$task_dir/progress.txt" >> "$output_dir/progress.log"
    done
}

# ── Progress display header ───────────────────────────────────────
show_batch_header() {
    local total="$1"
    local jobs="$2"
    local mem_info=""

    if command -v sysctl >/dev/null 2>&1; then
        local mem_gb
        mem_gb=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
        mem_info="${mem_gb}GB"
    elif [ -f /proc/meminfo ]; then
        local mem_gb
        mem_gb=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1048576 ))
        mem_info="${mem_gb}GB"
    fi

    echo ""
    tui_separator
    printf '  %b%baiki batch: %d tasks%b\n' "${TUI_WHITE:-}" "${TUI_BOLD:-}" "$total" "${TUI_RESET:-}"
    echo ""
    printf '  Jobs: %d   Timeout: %ds   Model: %s\n' "$jobs" "$TIMEOUT" "$MODEL"
    [ -n "$mem_info" ] && printf '  RAM: %s   ~1.5GB per job\n' "$mem_info"
    echo ""
    tui_separator
    echo ""
}

# ── Real-time TUI progress bar ───────────────────────────────────
# Sole owner of terminal output during task execution.
# Task completion lines are written to per-task files and merged later.
_progress_loop() {
    local total="$1"
    local counter_dir="$2"
    local bar_width=30

    while true; do
        local done_n fail_n running_n
        done_n=$(cat "$counter_dir/done" 2>/dev/null || echo 0)
        fail_n=$(cat "$counter_dir/fail" 2>/dev/null || echo 0)
        running_n=$(cat "$counter_dir/running" 2>/dev/null || echo 0)
        local completed=$((done_n + fail_n))
        local queued=$((total - completed - running_n))
        [ "$queued" -lt 0 ] && queued=0

        # Progress bar
        local pct=0
        [ "$total" -gt 0 ] && pct=$((completed * 100 / total))
        local filled=$((completed * bar_width / total))
        [ "$filled" -gt "$bar_width" ] && filled=$bar_width
        local empty=$((bar_width - filled))

        local bar=""
        local i=0
        while [ "$i" -lt "$filled" ]; do bar="${bar}█"; i=$((i + 1)); done
        i=0
        while [ "$i" -lt "$empty" ]; do bar="${bar}░"; i=$((i + 1)); done

        # Single \r overwrite (no newlines = no collision)
        printf '\r  Progress: %3d/%d [%s] %d%%  ✓%d ✗%d ⏳%d  ' \
            "$completed" "$total" "$bar" "$pct" "$done_n" "$fail_n" "$queued"

        [ "$completed" -ge "$total" ] && break
        sleep 2
    done
    printf '\n'
}

start_progress() {
    local total="$1"
    if [ "${TUI_AVAILABLE:-false}" = "true" ]; then
        _progress_loop "$total" "$_COUNTER_DIR" &
        _PROGRESS_PID=$!
        disown "$_PROGRESS_PID" 2>/dev/null || true
    fi
}

stop_progress() {
    if [ -n "${_PROGRESS_PID:-}" ]; then
        kill "$_PROGRESS_PID" 2>/dev/null || true
        wait "$_PROGRESS_PID" 2>/dev/null || true
        _PROGRESS_PID=""
        printf '\r\033[K'
    fi
}

# ── Print completed tasks after progress stops ───────────────────
print_task_results() {
    local output_dir="$1"
    local task_dir
    for task_dir in "$output_dir"/task-*/; do
        [ -d "$task_dir" ] || continue
        [ -f "$task_dir/result.json" ] || continue
        local task_id status duration exit_code task_model total_tasks
        task_id=$(jq -r '.id' "$task_dir/result.json" 2>/dev/null)
        status=$(jq -r '.status' "$task_dir/result.json" 2>/dev/null)
        duration=$(jq -r '.duration' "$task_dir/result.json" 2>/dev/null)
        exit_code=$(jq -r '.exit_code' "$task_dir/result.json" 2>/dev/null)
        task_model=$(jq -r '.model' "$task_dir/result.json" 2>/dev/null)

        if [ "$status" = "success" ]; then
            printf '  %b✓%b %-25s %3ds  %s\n' \
                "${TUI_GREEN:-}" "${TUI_RESET:-}" "$task_id" "$duration" "$task_model"
        elif [ "$status" = "timeout" ]; then
            printf '  %b✗%b %-25s timeout\n' \
                "${TUI_RED:-}" "${TUI_RESET:-}" "$task_id"
        else
            printf '  %b✗%b %-25s error(%s)\n' \
                "${TUI_RED:-}" "${TUI_RESET:-}" "$task_id" "$exit_code"
        fi
    done
}

# ── Generate summary ──────────────────────────────────────────────
generate_summary() {
    local total="$1"
    local batch_start="$2"
    local batch_end
    batch_end=$(date +%s)
    local total_duration=$((batch_end - batch_start))

    local done_count fail_count
    done_count=$(_counter_get done)
    fail_count=$(_counter_get fail)

    # Write summary JSON
    cat > "$OUTPUT_DIR/summary.json" << ENDJSON
{
  "total": ${total},
  "success": ${done_count},
  "failed": ${fail_count},
  "duration_seconds": ${total_duration},
  "jobs": ${JOBS},
  "model": "${MODEL}",
  "timeout": ${TIMEOUT},
  "output_dir": "${OUTPUT_DIR}"
}
ENDJSON

    # Display summary
    echo ""
    tui_separator
    printf '  %b%bBatch Complete%b\n' "${TUI_WHITE:-}" "${TUI_BOLD:-}" "${TUI_RESET:-}"
    echo ""
    printf '  Total:    %d tasks\n' "$total"
    printf '  %b✓ Success: %d%b\n' "${TUI_GREEN:-}" "$done_count" "${TUI_RESET:-}"
    if [ "$fail_count" -gt 0 ]; then
        printf '  %b✗ Failed:  %d%b\n' "${TUI_RED:-}" "$fail_count" "${TUI_RESET:-}"
    fi
    printf '  Duration: %dm%ds\n' $((total_duration / 60)) $((total_duration % 60))
    printf '  Output:   %s\n' "$OUTPUT_DIR"
    tui_separator
    echo ""
}

# ── Retry failed tasks ────────────────────────────────────────────
retry_failed() {
    local total="$1"

    [ ! -f "$OUTPUT_DIR/results.jsonl" ] && return 0

    local retry_file
    retry_file=$(mktemp /tmp/aiki-retry.XXXXXX)
    grep -v '"status":"success"' "$OUTPUT_DIR/results.jsonl" > "$retry_file" 2>/dev/null || true

    if [ ! -s "$retry_file" ]; then
        rm -f "$retry_file"
        return 0
    fi

    local fail_count
    fail_count=$(wc -l < "$retry_file" | tr -d ' ')
    tui_info "Retrying ${fail_count} failed tasks..."

    # Back up original results
    cp "$OUTPUT_DIR/results.jsonl" "$OUTPUT_DIR/results-before-retry.jsonl"

    # Reset fail counter
    echo "0" > "$_COUNTER_DIR/fail"

    # Re-run failed tasks (read from temp file, not pipe)
    local task_num=0
    while IFS= read -r result_line; do
        [ -z "$result_line" ] && continue
        task_num=$((task_num + 1))

        local task_id
        task_id=$(echo "$result_line" | sed 's/.*"id":"\([^"]*\)".*/\1/')

        # Find original task from JSONL
        local original_task
        original_task=$(grep "\"id\":\"${task_id}\"" "$TASK_FILE" 2>/dev/null | head -1)
        [ -z "$original_task" ] && continue

        local task_prompt task_model
        task_prompt=$(echo "$original_task" | jq -r '.prompt // empty' 2>/dev/null)
        task_model=$(echo "$original_task" | jq -r ".model // \"$MODEL\"" 2>/dev/null)
        [ -z "$task_prompt" ] && continue

        local task_dir="$OUTPUT_DIR/task-$(printf '%03d' "$task_num")-${task_id}-retry"

        sem_acquire
        run_task "$original_task" "$task_dir" "$task_id" "$task_model" "$task_prompt" "$task_num" "$fail_count" &
        _pids_add $!
    done < "$retry_file"
    rm -f "$retry_file"
    wait
}

# ── Dry run display ───────────────────────────────────────────────
show_dry_run() {
    local total="$1"

    echo ""
    tui_separator
    printf '  %b%bDry Run - %d tasks%b\n' "${TUI_WHITE:-}" "${TUI_BOLD:-}" "$total" "${TUI_RESET:-}"
    tui_separator
    echo ""

    local num=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        num=$((num + 1))

        local task_id task_prompt task_model
        task_id=$(echo "$line" | jq -r '.id // "unknown"' 2>/dev/null)
        task_prompt=$(echo "$line" | jq -r '.prompt // ""' 2>/dev/null)
        task_model=$(echo "$line" | jq -r ".model // \"$MODEL\"" 2>/dev/null)

        # Truncate prompt for display
        local display_prompt="$task_prompt"
        if [ ${#display_prompt} -gt 60 ]; then
            display_prompt="${display_prompt:0:57}..."
        fi

        printf '  %3d. %-20s [%s]  %s\n' "$num" "$task_id" "$task_model" "$display_prompt"
    done < "$TASK_FILE"

    echo ""
    printf '  Jobs: %s   Timeout: %ds   Retry: %d\n' "${JOBS:-auto}" "$TIMEOUT" "$RETRY_COUNT"
    printf '  Output: %s\n' "${OUTPUT_DIR:-.batch-results/TIMESTAMP}"
    echo ""
    tui_info "Run without --dry-run to execute"
    echo ""
}

# ── Cleanup ───────────────────────────────────────────────────────
cleanup() {
    stop_progress 2>/dev/null || true
    _pids_kill_all 2>/dev/null || true
    sem_destroy 2>/dev/null || true
    _counter_cleanup 2>/dev/null || true
    _pids_cleanup 2>/dev/null || true
}

trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

# ── Main ──────────────────────────────────────────────────────────
main() {
    parse_args "$@"

    # Validate: need either task file or --generate
    if [ -z "$TASK_FILE" ] && [ -z "$GENERATE_PROMPT" ]; then
        show_batch_help
        exit 1
    fi

    # Auto-detect jobs from RAM
    if [ -z "$JOBS" ]; then
        JOBS=$(detect_max_jobs)
    fi

    # Set output dir
    if [ -z "$OUTPUT_DIR" ]; then
        OUTPUT_DIR="${PROJECT_ROOT}/.batch-results/$(date '+%Y%m%d-%H%M%S')"
    fi

    # Generate mode
    if [ -n "$GENERATE_PROMPT" ]; then
        TASK_FILE="${OUTPUT_DIR}/generated-tasks.jsonl"
        mkdir -p "$OUTPUT_DIR"
        generate_tasks "$GENERATE_PROMPT" "$TASK_FILE"
    fi

    # Validate task file
    if [ ! -f "$TASK_FILE" ]; then
        tui_error "Task file not found: ${TASK_FILE}"
        exit 1
    fi

    # Count tasks
    local total
    total=$(grep -c '.' "$TASK_FILE" 2>/dev/null) || total=0
    if [ "$total" -eq 0 ]; then
        tui_error "No tasks found in ${TASK_FILE}"
        exit 1
    fi

    # Dry run
    if [ "$DRY_RUN" = "true" ]; then
        show_dry_run "$total"
        exit 0
    fi

    # Check for jq
    if ! command -v jq >/dev/null 2>&1; then
        tui_error "jq is required but not installed. Install with: brew install jq"
        exit 1
    fi

    # Check for claude CLI
    if ! command -v claude >/dev/null 2>&1; then
        tui_error "claude CLI is required but not found in PATH"
        exit 1
    fi

    # Setup
    mkdir -p "$OUTPUT_DIR"
    _counter_init
    _pids_init

    show_batch_header "$total" "$JOBS"

    # Initialize semaphore
    sem_init "$JOBS"

    local batch_start
    batch_start=$(date +%s)

    # Start real-time progress bar (sole terminal writer during execution)
    start_progress "$total"

    # Main task loop
    local task_num=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        task_num=$((task_num + 1))

        local task_id task_prompt task_model
        task_id=$(echo "$line" | jq -r '.id // "task-'"$task_num"'"' 2>/dev/null)
        task_prompt=$(echo "$line" | jq -r '.prompt // empty' 2>/dev/null)
        task_model=$(echo "$line" | jq -r ".model // \"$MODEL\"" 2>/dev/null)

        if [ -z "$task_prompt" ]; then
            tui_error "Skipping task ${task_num}: no prompt"
            continue
        fi

        local task_dir="$OUTPUT_DIR/task-$(printf '%03d' "$task_num")-${task_id}"

        sem_acquire
        run_task "$line" "$task_dir" "$task_id" "$task_model" "$task_prompt" "$task_num" "$total" &
        _pids_add $!
    done < "$TASK_FILE"

    # Wait for all tasks
    wait

    # Stop progress bar, then print completed task results
    stop_progress
    print_task_results "$OUTPUT_DIR"

    # Merge per-task results into results.jsonl + progress.log
    merge_results "$OUTPUT_DIR"

    # Retry failed tasks
    local fail_count
    fail_count=$(_counter_get fail)
    if [ "$fail_count" -gt 0 ] && [ "$RETRY_COUNT" -gt 0 ]; then
        local retry=0
        while [ "$retry" -lt "$RETRY_COUNT" ]; do
            retry=$((retry + 1))
            tui_info "Retry round ${retry}/${RETRY_COUNT}"
            start_progress "$fail_count"
            retry_failed "$total"
            stop_progress
            # Re-merge after retry
            merge_results "$OUTPUT_DIR"
            fail_count=$(_counter_get fail)
            [ "$fail_count" -eq 0 ] && break
        done
    fi

    # Summary
    generate_summary "$total" "$batch_start"
}

main "$@"
