#!/bin/bash
#
# enforce-delegation.sh - Hard-block enforcement for delegation rules
# PreToolUse hook for Edit|Write
#
# Exit codes:
#   0 = allow (whitelisted or no violation)
#   2 = BLOCK (delegation rule violated)
#

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# ── Escape hatch ─────────────────────────────────────────────────
if [ "${FORCE_CLAUDE:-}" = "1" ]; then
    exit 0
fi

# ── Extract file path from tool input ────────────────────────────
file_path=""
if [ -n "$TOOL_INPUT" ]; then
    # Extract file_path from JSON input
    file_path=$(echo "$TOOL_INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"$//')
fi

if [ -z "$file_path" ]; then
    exit 0
fi

# ── Whitelist check ──────────────────────────────────────────────
# These file types/paths are always allowed (Claude's domain)

# Get relative path
rel_path="${file_path#$PROJECT_DIR/}"

# Extension whitelist
ext="${rel_path##*.}"
case "$ext" in
    md|json|yaml|yml|toml|sh)
        exit 0
        ;;
esac

# Directory whitelist
case "$rel_path" in
    docs/*|.claude/*|.codex/*|.gemini/*|.grok/*|skills/*|scripts/*|tasks/*|benchmarks/*)
        exit 0
        ;;
    CLAUDE.md|AGENTS.md|GEMINI.md|GROK.md|README*)
        exit 0
        ;;
esac

# ── Pipeline phase check ────────────────────────────────────────
PHASE_FILE="${PROJECT_DIR}/.claude/.pipeline_phase"
if [ -f "$PHASE_FILE" ]; then
    phase=$(cat "$PHASE_FILE")
    case "$phase" in
        implement|test)
            echo "🚫 BLOCKED: Pipeline phase '${phase}' — implementation must be done by Codex.

This edit was blocked because the /project pipeline is in the '${phase}' phase,
which is delegated to Codex.

To proceed:
  1. Run \`/implement\` to delegate to Codex (\$0)
  2. Or override: \`export FORCE_CLAUDE=1\`"
            exit 2
            ;;
        requirements|design|review)
            # Claude's phases — allow
            exit 0
            ;;
    esac
fi

# ── Routing context check ───────────────────────────────────────
ROUTING_CTX="${PROJECT_DIR}/.claude/.routing_context"
if [ -f "$ROUTING_CTX" ]; then
    if grep -q "impl_detected=true" "$ROUTING_CTX" 2>/dev/null; then
        echo "🚫 BLOCKED: Implementation task detected — delegate to Codex.

The current prompt was identified as an implementation task.
Editing source files directly violates the delegation rules.

To proceed:
  1. Run \`/implement\` to delegate to Codex (\$0)
  2. Or override: \`export FORCE_CLAUDE=1\`
  3. If this is NOT implementation, rephrase your request without implementation keywords"
        exit 2
    fi
fi

# ── Session counter check ───────────────────────────────────────
SESSION_EDIT_FILE="${PROJECT_DIR}/.claude/.session_edit_count"
SESSION_NEW_FILE="${PROJECT_DIR}/.claude/.session_new_files"
TOOL_NAME="${CLAUDE_TOOL_NAME:-Edit}"

# Count new file creations (Write tool to non-existent files)
if [ "$TOOL_NAME" = "Write" ]; then
    if [ ! -f "$file_path" ]; then
        new_count=0
        [ -f "$SESSION_NEW_FILE" ] && new_count=$(cat "$SESSION_NEW_FILE")
        new_count=$((new_count + 1))
        echo "$new_count" > "$SESSION_NEW_FILE"

        if [ "$new_count" -ge 3 ]; then
            echo "🚫 BLOCKED: ${new_count} new source files created in this session.

Creating 3+ new files indicates a large implementation task.
This should be delegated to Codex per delegation rules.

To proceed:
  1. Run \`/implement\` to delegate to Codex (\$0)
  2. Or override: \`export FORCE_CLAUDE=1\`
  3. Reset counter: \`rm .claude/.session_new_files\`"
            exit 2
        fi
    fi
fi

# Count unique file edits
edit_count=0
[ -f "$SESSION_EDIT_FILE" ] && edit_count=$(cat "$SESSION_EDIT_FILE")

# Check if this file was already counted
EDIT_LOG="${PROJECT_DIR}/.claude/.session_edit_log"
if ! grep -qF "$rel_path" "$EDIT_LOG" 2>/dev/null; then
    echo "$rel_path" >> "$EDIT_LOG"
    edit_count=$((edit_count + 1))
    echo "$edit_count" > "$SESSION_EDIT_FILE"
fi

if [ "$edit_count" -ge 5 ]; then
    echo "🚫 BLOCKED: ${edit_count} unique source files edited in this session.

Editing 5+ source files indicates a large implementation task.
This should be delegated to Codex per delegation rules.

Files edited so far:
$(cat "$EDIT_LOG" 2>/dev/null | head -10 | sed 's/^/  - /')

To proceed:
  1. Run \`/implement\` to delegate to Codex (\$0)
  2. Or override: \`export FORCE_CLAUDE=1\`
  3. Reset counter: \`rm .claude/.session_edit_count .claude/.session_edit_log\`"
    exit 2
fi

# ── Default: allow ───────────────────────────────────────────────
exit 0
