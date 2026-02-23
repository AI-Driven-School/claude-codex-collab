# @steipete (Peter Steinberger) - AI Development Methodology Research

> Research date: 2026-02-23
> Sources: steipete.me blog, X/Twitter, Pragmatic Engineer podcast, TechCrunch, web search

---

## Who is Peter Steinberger?

- Austrian software developer based in Vienna and London
- Founded PSPDFKit in 2011 (successful exit in 2021)
- Creator of OpenClaw (formerly Clawdbot/Moltbot) - viral AI personal assistant agent
- Joined OpenAI in February 2026 to work on "bringing agents to everyone"
- One of the most prolific and vocal advocates of "agentic engineering"
- Made 6,600+ commits in January 2026 alone, with AI writing ~100% of code
- Blog: https://steipete.me | GitHub: https://github.com/steipete

---

## 1. Tools He Uses

### Primary Stack
| Tool | Role | Notes |
|------|------|-------|
| **Claude Code** | Primary coding agent | Runs with `--dangerously-skip-permissions` |
| **Ghostty** | Terminal | Replaced VS Code terminal (freezes on large pastes) |
| **GPT-5 / Codex** | Plan review, strategy | "Excels at reviewing plans" |
| **Gemini (AI Studio)** | Codebase analysis, spec generation | 1M token context window |
| **VS Code** | Code browsing (secondary) | Not primary IDE |
| **Cursor** | Reviews, alternative AI backend | Switchable AI models |

### Custom Tools He Built
| Tool | Purpose |
|------|---------|
| **OpenClaw** | Personal AI assistant (WhatsApp, Telegram, Slack, iMessage, etc.) |
| **VibeTunnel** | Turn any browser into your terminal |
| **Vibe Meter / CodexBar** | Monitor AI coding costs across 15+ providers |
| **Peekaboo** | Lightning-fast macOS screenshots for AI agents (MCP) |
| **Poltergeist** | Universal build watcher |
| **Demark** | HTML to Markdown converter |
| **llm.codes** | Make Apple Docs AI-readable |

### MCP Tools (Model Context Protocol)
- Peekaboo: Screenshot analysis for visual debugging
- Conduit: Robust file manipulation
- Terminator: Managing external processes
- Automator: AppleScript integration
- Note: He removed most MCPs later - "Claude sometimes would go off spinning up Playwright unasked"

---

## 2. His Workflow / Development Approach

### Core Philosophy: "Just Talk To It"
- Against elaborate workflows and tool proliferation
- Straightforward communication with AI models
- Intuition over optimization
- "I can just write 'let's discuss' or 'give me options' and it will diligently wait until I approve it"

### The "Agentic Engineering" Workflow

**Step 1: Planning**
- Converse with the model, explore options
- Smaller tasks: handle immediately
- Bigger tasks: write in a file, have GPT-5 review the plan
- Use plan mode and iterate

**Step 2: Specification (for larger projects)**
- Voice-dictate ideas using Flow/Whisper Flow
- Use Gemini AI Studio to transform voice notes into structured specs
- "Peer review by AI" - have a second Gemini instance critique the spec
- Iterate 3-5 rounds until questions become specialized

**Step 3: Implementation**
- Write "build" to trigger implementation
- Run 1-2 agents during refactoring, ~4 for cleanup/tests/UI work
- Monitor streaming output (watches code, doesn't read it line-by-line)
- Queue messages rather than interrupting mid-task

**Step 4: Testing & Iteration**
- Write tests IN THE SAME CONTEXT as the feature (context is "precious")
- Use screenshots for visual debugging (more effective than text descriptions)
- Build, test, feel the result, then refine

**Step 5: Shipping**
- Commits directly to main
- Avoids issue trackers ("prompt immediately instead")
- Starts every project with CLI + model before building UI

### Parallel Agent Strategy
- 3-8 terminal windows with concurrent agents
- 1-2 agents for refactoring
- ~4 agents for cleanup, tests, UI work (sweet spot)
- Pick work areas "carefully so you can work on multiple areas without much cross-pollination"
- Requires discipline around atomic git commits
- Avoids git worktrees ("slowed me down")

### Context Management
- CLAUDE.md with minimal, practical one-liners (e.g., "logs: axiom or vercel cli")
- Services with CLIs preferred (vercel, psql, gh, axiom) - agents use them with one line in CLAUDE.md
- Cross-project references ("look at ../project-folder")
- Statusline + session ID for account switching/restart
- Docs folders per project

---

## 3. Specific Techniques, Tips & Frameworks

### Key Principles
1. **"Less is more"** - Eliminate unnecessary tooling, MCPs, complexity
2. **"Context is currency"** - Quality of AI output depends directly on context provided
3. **"Model selection matters"** - Different AI systems excel at different tasks; switch strategically
4. **"Code is cheap to generate and discard"** - Lowers experimentation costs dramatically
5. **"You become an architect, a guide, a refiner"** - Not a coder anymore

### Practical Tips
- **Use screenshots** instead of text descriptions for debugging
- **Trigger words**: "take your time" and "comprehensive" for complex problems
- **Preserve intent** through code comments on tricky sections
- **If you prompt something twice, turn it into a command** (/commit, /review, /prime)
- **Run with `--dangerously-skip-permissions`** for uninterrupted flow (with hourly backups)
- **Monitor agents actively** to prevent "drifting off" - background agents impractical
- **Prompt precision**: Focused, unambiguous instructions > comprehensive multi-point requests
- **Voice-first brainstorming**: Capture ideas fluidly before structuring via AI

### Codebase Understanding Workflow (Gemini)
1. Convert repo to markdown using repo2txt
2. Drag into Google AI Studio (1M token context)
3. Ask analytical questions ("What's notable about this project?")
4. Use "two-context technique" - one Gemini critiques specs, another maintains history
5. Convert finalized spec into Claude Code implementation instructions

### Essential Reading He Recommends
- "How to Use Claude Code Effectively" (Philipp Spiess)
- "Claude Code Best Practices" (Anthropic)
- "Agentic Coding: The Future of Software Development" (Armin Ronacher)
- "A Practical Guide to Agentic Computing" (Mario Zechner)
- "MCP vs CLI: Tool Comparison" (Mario Zechner) - CLI often outperforms MCP

---

## 4. What Makes His Approach Notable / Viral

### The "I Ship Code I Don't Read" Philosophy
- Featured on The Pragmatic Engineer podcast
- 100% AI-generated code, but he still thinks deeply about architecture
- Provoked massive debate about the future of software engineering
- Rejects the term "vibe coding" - calls it "an insult to the discipline"
- Prefers "agentic engineering" - implies intentionality and expertise

### Prolific Output
- 6,600+ commits in January 2026
- 37 blog posts in 2025 alone on AI development topics
- Built dozens of tools and projects using AI
- Live-coded two complete apps in 3 hours (5,000+ lines, zero manual code)

### "Claude Code is My Computer"
- Describes Claude Code as "a universal computer interface that happens to run in text"
- Runs with `--dangerously-skip-permissions` on bare macOS (not Docker)
- Zero incidents after months of use
- Viral take that polarized the developer community

### From Solo Builder to OpenAI
- Built OpenClaw as a solo project that went viral
- Sam Altman personally recruited him ("a genius with amazing ideas")
- Joined OpenAI February 2026 to democratize AI agents
- OpenClaw moved to a foundation, stays open source

### Community Building
- Created "Claude Code Anonymous" meetup format
- Curates "Essential Reading for Agentic Engineers" monthly
- Active on X with strong developer following
- Live workshops demonstrating vibe coding

---

## 5. Projects Built Using AI

| Project | Description | Tech |
|---------|-------------|------|
| **OpenClaw** | Personal AI assistant across all messaging platforms | Multi-model, open source |
| **Vibe Meter** | AI cost tracking macOS menu bar app | SwiftUI + Electron |
| **CodexBar** | Agent usage limits display (15+ providers) | macOS |
| **VibeTunnel** | Browser-to-terminal bridge | TypeScript |
| **Peekaboo** | Screenshot tool for AI agents | macOS CLI/MCP |
| **Poltergeist** | Universal build watcher | - |
| **Demark** | HTML to Markdown converter | - |
| **llm.codes** | Apple Docs made AI-readable | - |
| **stats.store** | Privacy-first Sparkle analytics | - |
| **sweetistics.com** | AI-powered Twitter analytics platform | - |
| **Arena** | Real-time collaborative AI dev (live-coded) | - |

---

## Key Takeaways for Our Project

1. **CLAUDE.md should be minimal and practical** - One-liners, not essays. CLI tool references, not documentation.
2. **Parallel agents are powerful** - 3-4 concurrent agents on non-overlapping areas is the sweet spot.
3. **CLI tools > MCP servers** - Prefer services with CLIs that agents can use directly.
4. **Model routing matters** - Different models for different tasks (exactly what ai4dev does).
5. **Gemini for specs, Claude for implementation** - Aligns with our workflow.
6. **Voice + AI spec generation** is an underexplored workflow accelerator.
7. **Screenshots for debugging** - Visual context is more effective than text for multimodal models.
8. **"If you prompt it twice, make it a command"** - Automate repeated prompt patterns.

---

## Sources

- https://steipete.me/posts/2025/optimal-ai-development-workflow
- https://steipete.me/posts/2025/the-future-of-vibe-coding
- https://steipete.me/posts/2025/understanding-codebases-with-ai-gemini-workflow
- https://steipete.me/posts/just-talk-to-it
- https://steipete.me/posts/2025/essential-reading
- https://steipete.me/posts/2025/shipping-at-inference-speed
- https://steipete.me/posts/2025/claude-code-is-my-computer
- https://steipete.me/posts/2026/openclaw
- https://newsletter.pragmaticengineer.com/p/the-creator-of-clawd-i-ship-code
- https://techcrunch.com/2026/02/15/openclaw-creator-peter-steinberger-joins-openai/
