#!/usr/bin/env bash
# record-real.sh - Record the terminal demo and convert to GIF/MP4
# Usage: bash landing/record-real.sh
#
# Dependencies:
#   brew install asciinema   # Terminal recording
#   brew install agg         # .cast → GIF (recommended)
#   brew install ffmpeg      # GIF → MP4 conversion
#
# Alternative GIF tools (if agg unavailable):
#   npm install -g svg-term-cli   # .cast → SVG → can screenshot
#   pip install termtosvg          # Alternative recorder

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIMULATE_SCRIPT="${SCRIPT_DIR}/simulate-demo.sh"
CAST_FILE="${SCRIPT_DIR}/viral-demo.cast"
OUTPUT_GIF="${SCRIPT_DIR}/viral-demo.gif"
OUTPUT_MP4="${SCRIPT_DIR}/viral-demo.mp4"

# ===== Dependency checks =====
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "❌ $1 not found. Install with: $2"
    return 1
  fi
  echo "✓ $1 found"
  return 0
}

echo "🔍 Checking dependencies..."
deps_ok=true
check_cmd asciinema "brew install asciinema" || deps_ok=false
check_cmd agg "brew install agg" || deps_ok=false
check_cmd ffmpeg "brew install ffmpeg" || deps_ok=false

if [ "$deps_ok" = false ]; then
  echo ""
  echo "Install missing dependencies and try again."
  echo "Quick install: brew install asciinema agg ffmpeg"
  exit 1
fi
echo ""

# ===== Step 1: Record with asciinema =====
echo "🎬 Step 1: Recording terminal demo..."
echo "   Output: ${CAST_FILE}"
echo ""

# Set terminal size for consistent recording (80 cols is standard, 24 rows)
export COLUMNS=80
export LINES=24

asciinema rec \
  --overwrite \
  --cols 80 \
  --rows 24 \
  --command "bash '${SIMULATE_SCRIPT}'" \
  "${CAST_FILE}"

echo ""
echo "✅ Recording saved: ${CAST_FILE}"
echo ""

# ===== Step 2: Convert to GIF =====
echo "🎨 Step 2: Converting to GIF..."
echo "   Output: ${OUTPUT_GIF}"
echo ""

agg \
  --font-family "JetBrains Mono,SF Mono,Menlo,monospace" \
  --font-size 16 \
  --theme asciinema \
  --speed 1.0 \
  --fps-cap 15 \
  --last-frame-duration 3 \
  "${CAST_FILE}" \
  "${OUTPUT_GIF}"

echo "✅ GIF created: ${OUTPUT_GIF}"
echo ""

# ===== Step 3: Convert GIF to MP4 =====
echo "🎥 Step 3: Converting to MP4..."
echo "   Output: ${OUTPUT_MP4}"
echo ""

ffmpeg -y \
  -i "${OUTPUT_GIF}" \
  -movflags faststart \
  -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 \
  -crf 20 \
  -preset slow \
  "${OUTPUT_MP4}" \
  2>/dev/null

echo "✅ MP4 created: ${OUTPUT_MP4}"
echo ""

# ===== Report =====
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Done!"
echo ""

report_file() {
  local label="$1"
  local filepath="$2"
  if [ -f "$filepath" ]; then
    local size
    size=$(du -h "$filepath" | cut -f1 | xargs)
    echo "  ${label}: ${filepath} (${size})"
  fi
}

report_file "Cast" "${CAST_FILE}"
report_file "GIF " "${OUTPUT_GIF}"
report_file "MP4 " "${OUTPUT_MP4}"

echo ""
echo "📋 Next steps:"
echo "   1. Preview: open '${OUTPUT_GIF}'"
echo "   2. Check sizes: GIF < 10MB, MP4 < 5MB"
echo "   3. Post GIF to GitHub README"
echo "   4. Post MP4 natively to X/Twitter and Reddit"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
