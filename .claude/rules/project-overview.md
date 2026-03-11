---
paths:
  - '**/*'
---
# Project Overview

**aiki**: 4-AI collaborative development workflow template using Claude + Codex + Gemini + Grok

- Claude: Design & review
- Codex: Implementation & testing (ChatGPT Pro, $0)
- Gemini: Large-scale analysis (free)
- Grok: Real-time information & trend research (xAI API)

## Key Directories

```
docs/
├── requirements/   # Requirements (created by Claude)
├── specs/          # UI specs (created by Claude)
├── api/            # API design (created by Claude)
├── decisions/      # Important decision records
└── reviews/        # Code review results

.claude/docs/
├── DESIGN.md       # Design principles
└── research/       # Gemini & Grok research results

skills/             # Custom skills
scripts/            # Utility scripts
benchmarks/         # Benchmark results & sample implementations
landing/            # Landing page
```

## Design Documents

Before implementing, check:
- `.claude/docs/DESIGN.md` - Design principles
- `docs/requirements/` - Requirements
- `docs/specs/` - UI specifications
- `docs/api/` - API design

## Communication

- Report results in a clear, structured format
- Ask questions before starting if anything is unclear
- Output in a format that helps other AIs make decisions
