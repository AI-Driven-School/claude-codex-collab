# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (main) | Yes |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: Create a [private security advisory](https://github.com/AI-Driven-School/claude-codex-collab/security/advisories/new)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 72 hours.

## Security Considerations

### Skills execute code

Claude Code skills can execute arbitrary code via `Bash` tool calls. Before installing third-party skills:

- Review the SKILL.md content
- Check any scripts in `scripts/` directories
- Verify the source repository is trusted

### AI delegation

This project delegates tasks to external AI services (Codex, Gemini). Be aware that:

- Code and context are sent to third-party APIs
- Do not include secrets, credentials, or sensitive data in delegated tasks
- Review AI-generated code before deploying to production

### Shell scripts

All shell scripts in this project:

- Do not transmit data to external servers (except via AI CLIs)
- Do not modify system files outside the project directory
- Use `set -e` for fail-fast behavior
