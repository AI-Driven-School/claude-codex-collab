# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Local model support via Ollama (`delegate.sh ollama generate/review`)
- Cost comparison documentation (`docs/COST_COMPARISON.md`)
- OpenCode compatibility documentation and testing
- IDE integration templates (`templates/vscode-tasks.json`, `.cursor/rules/`)
- GitHub Actions AI code review workflow (`ai-review.yml`)
- Social media promotion drafts (`docs/SOCIAL_MEDIA_POSTS.md`)
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, TEAM_USAGE.md
- GitHub Actions CI (ShellCheck, skill validation)
- Issue and PR templates
- GitHub topics: agent-skills, claude-code, claude-skills

### Changed
- Skills now comply with [Agent Skills open standard](https://agentskills.io/specification)
- All skill descriptions improved with "what + when to use" format
- Skills located in `.claude/skills/` (Agent Skills standard directory format)
- README updated with compatibility matrix (OpenCode, Cursor, VS Code)
- Agent Skills compatibility expanded: Claude Code, Codex CLI, OpenCode, Cursor

### Fixed
- Install script CLI package references
- Skills directory format (single file -> directory/SKILL.md)

## [1.0.0] - 2026-02-03

### Added
- Initial release
- 13 Claude Code skills (project, requirements, spec, api, implement, test, review, analyze, research, frontend-design, mockup, mockup-swift, checkpointing)
- Claude Code Orchestra (Hooks + Rules + Knowledge Base)
- MCP Server for automatic AI delegation
- Installation scripts (install.sh, install-fullstack.sh)
- Comprehensive documentation (Getting Started, Tutorial, Commands)
- Benchmark results and case study (StressAIAgent)
- Landing page and promotional materials
