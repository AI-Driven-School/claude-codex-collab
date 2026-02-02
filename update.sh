#!/bin/bash
# ============================================
# claude-codex-collab アップデートスクリプト
# ============================================
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/AI-Driven-School/claude-codex-collab/main/update.sh | bash
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

REPO_URL="https://raw.githubusercontent.com/AI-Driven-School/claude-codex-collab/main"
LATEST_VERSION="6.1.0"

echo -e "${CYAN}"
echo "┌─────────────────────────────────────────────────────────┐"
echo "│   claude-codex-collab アップデート                      │"
echo "│   Latest: v${LATEST_VERSION}                                        │"
echo "└─────────────────────────────────────────────────────────┘"
echo -e "${NC}"

# 現在のバージョンを確認
CURRENT_VERSION="unknown"
if [ -f "CLAUDE.md" ]; then
    CURRENT_VERSION=$(grep -o 'v[0-9]\+\.[0-9]\+' CLAUDE.md 2>/dev/null | head -1 || echo "unknown")
fi

echo -e "現在のバージョン: ${YELLOW}${CURRENT_VERSION}${NC}"
echo -e "最新バージョン:   ${GREEN}v${LATEST_VERSION}${NC}"
echo ""

# CLAUDE.md が存在するか確認
if [ ! -f "CLAUDE.md" ]; then
    echo -e "${RED}エラー: CLAUDE.md が見つかりません${NC}"
    echo "claude-codex-collab がインストールされたディレクトリで実行してください"
    exit 1
fi

# バックアップ
echo "バックアップを作成中..."
BACKUP_DIR=".claude-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp CLAUDE.md "$BACKUP_DIR/" 2>/dev/null || true
cp AGENTS.md "$BACKUP_DIR/" 2>/dev/null || true
cp -r scripts "$BACKUP_DIR/" 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} $BACKUP_DIR"

echo ""
echo "アップデート中..."

# CLAUDE.md を更新
echo -e "  ${BLUE}→${NC} CLAUDE.md"
curl -fsSL "$REPO_URL/install-fullstack.sh" | sed -n '/^cat > CLAUDE.md/,/^EOF$/p' | sed '1d;$d' > CLAUDE.md.new

# 既存のカスタム設定を保持（## プロジェクト固有 セクション以降）
if grep -q "## プロジェクト固有" CLAUDE.md 2>/dev/null; then
    echo "" >> CLAUDE.md.new
    sed -n '/## プロジェクト固有/,$p' CLAUDE.md >> CLAUDE.md.new
fi

mv CLAUDE.md.new CLAUDE.md
echo -e "  ${GREEN}✓${NC} CLAUDE.md 更新完了"

# AGENTS.md を更新
echo -e "  ${BLUE}→${NC} AGENTS.md"
curl -fsSL "$REPO_URL/install-fullstack.sh" | sed -n '/^cat > AGENTS.md/,/^EOF$/p' | sed '1d;$d' > AGENTS.md
echo -e "  ${GREEN}✓${NC} AGENTS.md 更新完了"

# delegate.sh を更新
echo -e "  ${BLUE}→${NC} scripts/delegate.sh"
mkdir -p scripts
curl -fsSL "$REPO_URL/install-fullstack.sh" | sed -n "/^cat > scripts\/delegate.sh/,/^SCRIPT_EOF$/p" | sed '1d;$d' > scripts/delegate.sh
chmod +x scripts/delegate.sh
echo -e "  ${GREEN}✓${NC} scripts/delegate.sh 更新完了"

# スキルを更新
echo -e "  ${BLUE}→${NC} .claude/skills/"
mkdir -p .claude/skills
for skill in project implement test review analyze research requirements spec api; do
    curl -fsSL "$REPO_URL/install-fullstack.sh" | sed -n "/^cat > .claude\/skills\/${skill}.md/,/^EOF$/p" | sed '1d;$d' > ".claude/skills/${skill}.md" 2>/dev/null || true
done
echo -e "  ${GREEN}✓${NC} スキル更新完了"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}アップデート完了！ v${LATEST_VERSION}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}v6.1 の新機能:${NC}"
echo -e "  ${BLUE}•${NC} サブエージェント活用ルールを追加"
echo -e "    - Task(Explore) でコード探索"
echo -e "    - Task(Plan) で計画立案"
echo -e "    - 複数Taskの並列実行"
echo ""
echo -e "${CYAN}バックアップ:${NC}"
echo -e "  ${BLUE}${BACKUP_DIR}/${NC}"
echo ""
echo -e "詳細: ${BLUE}https://github.com/AI-Driven-School/claude-codex-collab/releases${NC}"
echo ""
