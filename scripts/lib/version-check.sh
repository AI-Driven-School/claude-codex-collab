#!/bin/bash
# ============================================
# AI CLI Version Compatibility Checker
# ============================================
# Checks installed AI CLI versions against the
# compatibility matrix in .ai-versions.json.
#
# Usage:
#   source scripts/lib/version-check.sh
#   check_all_versions
#   check_ai_compatibility "claude"
# ============================================

_VC_GREEN='\033[0;32m'
_VC_YELLOW='\033[1;33m'
_VC_RED='\033[0;31m'
_VC_CYAN='\033[0;36m'
_VC_NC='\033[0m'
_VC_BOLD='\033[1m'

# Compare two semver strings: returns 0 if v1 >= v2
version_gte() {
    local v1="$1"
    local v2="$2"

    # Extract major.minor.patch
    local v1_major v1_minor v1_patch
    IFS='.' read -r v1_major v1_minor v1_patch <<< "$v1"
    v1_major="${v1_major:-0}"
    v1_minor="${v1_minor:-0}"
    v1_patch="${v1_patch:-0}"

    local v2_major v2_minor v2_patch
    IFS='.' read -r v2_major v2_minor v2_patch <<< "$v2"
    v2_major="${v2_major:-0}"
    v2_minor="${v2_minor:-0}"
    v2_patch="${v2_patch:-0}"

    if [ "$v1_major" -gt "$v2_major" ]; then return 0; fi
    if [ "$v1_major" -lt "$v2_major" ]; then return 1; fi
    if [ "$v1_minor" -gt "$v2_minor" ]; then return 0; fi
    if [ "$v1_minor" -lt "$v2_minor" ]; then return 1; fi
    if [ "$v1_patch" -ge "$v2_patch" ]; then return 0; fi
    return 1
}

# Get the installed version of an AI CLI tool
# Returns version string or "not_installed"
get_ai_version() {
    local tool="$1"
    local version_cmd=""

    case "$tool" in
        claude) version_cmd="claude --version" ;;
        codex)  version_cmd="codex --version" ;;
        gemini) version_cmd="gemini --version" ;;
        *)
            echo "unknown"
            return 1
            ;;
    esac

    if ! command -v "$tool" &>/dev/null; then
        echo "not_installed"
        return 1
    fi

    local raw_version
    raw_version=$($version_cmd 2>/dev/null | head -1)
    # Extract version number (handles formats like "claude v1.2.3" or "1.2.3")
    local version
    version=$(echo "$raw_version" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

    if [ -z "$version" ]; then
        echo "unknown"
        return 0
    fi

    echo "$version"
}

# Check compatibility of a single tool
# Returns: ok, below_min, above_tested, not_installed, unknown
check_ai_compatibility() {
    local tool="$1"
    local versions_file="${2:-.ai-versions.json}"

    if [ ! -f "$versions_file" ]; then
        echo "no_config"
        return 0
    fi

    local installed_version
    installed_version=$(get_ai_version "$tool")

    if [ "$installed_version" = "not_installed" ]; then
        echo "not_installed"
        return 0
    fi

    if [ "$installed_version" = "unknown" ]; then
        echo "unknown"
        return 0
    fi

    # Parse min and max versions from JSON (portable, no jq required)
    local min_version max_tested
    min_version=$(grep -A5 "\"$tool\"" "$versions_file" | grep '"min_version"' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    max_tested=$(grep -A5 "\"$tool\"" "$versions_file" | grep '"max_tested"' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

    if [ -z "$min_version" ] || [ -z "$max_tested" ]; then
        echo "unknown"
        return 0
    fi

    if ! version_gte "$installed_version" "$min_version"; then
        echo "below_min"
        return 0
    fi

    if ! version_gte "$max_tested" "$installed_version"; then
        echo "above_tested"
        return 0
    fi

    echo "ok"
}

# Display version compatibility report for all tools
check_all_versions() {
    local versions_file="${1:-.ai-versions.json}"

    echo -e "${_VC_BOLD}AI CLI Compatibility Check${_VC_NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    for tool in claude codex gemini; do
        local version
        version=$(get_ai_version "$tool")
        local compat
        compat=$(check_ai_compatibility "$tool" "$versions_file")

        local min_version max_tested
        if [ -f "$versions_file" ]; then
            min_version=$(grep -A5 "\"$tool\"" "$versions_file" | grep '"min_version"' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
            max_tested=$(grep -A5 "\"$tool\"" "$versions_file" | grep '"max_tested"' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi

        case "$compat" in
            ok)
                echo -e "  ${_VC_GREEN}[OK]${_VC_NC}      $tool ${_VC_CYAN}v${version}${_VC_NC} (range: ${min_version}-${max_tested})"
                ;;
            below_min)
                echo -e "  ${_VC_RED}[OLD]${_VC_NC}     $tool ${_VC_RED}v${version}${_VC_NC} (minimum: ${min_version})"
                echo -e "            Update: $(grep -A8 "\"$tool\"" "$versions_file" | grep '"install_command"' | sed 's/.*": "//;s/".*//')"
                ;;
            above_tested)
                echo -e "  ${_VC_YELLOW}[NEW]${_VC_NC}     $tool ${_VC_YELLOW}v${version}${_VC_NC} (tested up to: ${max_tested})"
                echo -e "            May work, but not yet tested with this version."
                ;;
            not_installed)
                echo -e "  ${_VC_YELLOW}[MISS]${_VC_NC}    $tool not installed"
                if [ -f "$versions_file" ]; then
                    echo -e "            Install: $(grep -A8 "\"$tool\"" "$versions_file" | grep '"install_command"' | sed 's/.*": "//;s/".*//')"
                fi
                ;;
            *)
                echo -e "  ${_VC_YELLOW}[?]${_VC_NC}       $tool v${version} (unable to check)"
                ;;
        esac
    done

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}
