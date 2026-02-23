#!/usr/bin/env bash
# semaphore.sh - FIFO-based bash semaphore for concurrency control
# Bash 3.2+ compatible. No external dependencies.
#
# Usage:
#   source scripts/lib/semaphore.sh
#   sem_init 8          # Allow up to 8 concurrent jobs
#   for task in ...; do
#     sem_acquire
#     run_task &
#     # Call sem_release inside run_task when done
#   done
#   wait
#   sem_destroy

# ── Guard: only load once ──────────────────────────────────────────
if [ "${_SEM_LOADED:-}" = "true" ]; then return 0 2>/dev/null || true; fi
_SEM_LOADED=true

_SEM_FIFO=""
_SEM_FD=""

# ── sem_init ──────────────────────────────────────────────────────
# Create FIFO and pre-fill with N tokens
# Usage: sem_init <max_jobs>
sem_init() {
    local max_jobs="${1:?sem_init requires max_jobs}"

    _SEM_FIFO=$(mktemp -u /tmp/aiki-sem.XXXXXX)
    mkfifo "$_SEM_FIFO"

    # Open FIFO on fd 3 for read+write (non-blocking setup)
    exec 3<>"$_SEM_FIFO"
    _SEM_FD=3

    # Write N tokens (each is a single newline)
    local i=0
    while [ "$i" -lt "$max_jobs" ]; do
        printf '\n' >&3
        i=$((i + 1))
    done
}

# ── sem_acquire ───────────────────────────────────────────────────
# Consume one token (blocks if none available)
sem_acquire() {
    local _token
    IFS= read -r -u 3 _token
}

# ── sem_release ───────────────────────────────────────────────────
# Return one token to the pool
sem_release() {
    printf '\n' >&3
}

# ── sem_destroy ───────────────────────────────────────────────────
# Close fd and remove FIFO
sem_destroy() {
    exec 3>&- 2>/dev/null || true
    [ -n "$_SEM_FIFO" ] && rm -f "$_SEM_FIFO" 2>/dev/null || true
    _SEM_FIFO=""
    _SEM_FD=""
}
