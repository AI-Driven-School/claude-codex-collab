# Reddit 投稿原稿

---

## r/ClaudeAI 向け

### Title
```
I built a 3-AI collaboration system (Claude + Codex + Gemini) - reduces costs by 75%
```

### Body
```
Hey everyone! I've been experimenting with delegating work between multiple AI coding assistants, and wanted to share what I came up with.

## The Problem

Using Claude Code for everything gets expensive - especially for implementation and test generation where there's a lot of code output.

## The Solution

I created a workflow that delegates tasks based on each AI's strengths:

| AI | Role | Cost |
|---|---|---|
| **Claude** | Design, Review, Decisions | Pay per use |
| **Codex** | Implementation, Tests | $0 (included in ChatGPT Pro) |
| **Gemini** | Large-scale analysis | Free |

## How it works

Single command: `/project <feature-name>`

```
[1/6] Requirements  → Claude generates specs
[2/6] Design        → Claude creates API/UI specs
[3/6] Implementation → Codex builds it ($0)
[4/6] Tests         → Codex generates E2E tests ($0)
[5/6] Review        → Claude reviews code
[6/6] Deploy        → Approval then ship
```

## Real Example

I built an "Organization Analytics AI Dashboard" for a mental health SaaS using this workflow. It generated:

- Requirements doc
- OpenAPI spec
- UI design spec
- Backend API (FastAPI)
- Frontend (Next.js)
- 10 E2E tests
- Code review doc

All from one `/project 組織分析AI` command.

## Cost Comparison

- **Claude only**: ~$1.00 per feature
- **3-AI collaboration**: ~$0.25 per feature (75% reduction)

## Open Source

GitHub: https://github.com/AI-Driven-School/claude-codex-collab

Would love feedback! Especially interested in:
- Other ways to optimize the workflow
- Additional AI tools that could be integrated
- Your experiences with multi-AI development

---

**Requirements:**
- Claude Code CLI
- ChatGPT Pro ($200/mo) for Codex
- Gemini CLI (free)
```

### Flair
```
Project/Tool
```

---

## r/SideProject 向け

### Title
```
I made an open-source CLI that combines Claude + Codex + Gemini for faster development
```

### Body
```
Hey r/SideProject!

As a solo developer, I was spending too much on AI coding tools. So I built a system that delegates work between 3 AIs based on their strengths.

## What it does

One command (`/project <feature>`) runs a 6-phase workflow:

1. **Requirements** - Claude writes the spec
2. **Design** - Claude creates API & UI specs
3. **Implementation** - Codex codes it (free with ChatGPT Pro)
4. **Tests** - Codex generates E2E tests (also free)
5. **Review** - Claude reviews the code
6. **Deploy** - Ship when approved

## Why 3 AIs?

| Task | Best AI | Cost |
|------|---------|------|
| Thinking/Design | Claude | $ |
| Coding | Codex | $0 |
| Analysis | Gemini | $0 |

Result: **75% cost reduction** compared to using Claude for everything.

## Proof it works

Built a full dashboard feature for my SaaS using this workflow:
- Generated 8 files (backend, frontend, tests, docs)
- 10 E2E test cases
- All design docs included

**As a solo dev, I now have documentation I'd never write myself.**

## Links

- GitHub: https://github.com/AI-Driven-School/claude-codex-collab
- Demo GIF in the README

It's MIT licensed, totally free. Would appreciate a ⭐ if you find it useful!

Happy to answer questions about the implementation.
```

### Flair
```
Built with AI / Open Source
```

---

## r/ChatGPT 向け（オプション）

### Title
```
Using Codex (ChatGPT Pro) + Claude + Gemini together - my 3-AI development workflow
```

### Body
```
Found a way to get more value from my ChatGPT Pro subscription by using Codex alongside Claude and Gemini.

**The setup:**
- Claude Code: Design & review (pay per use)
- Codex: Implementation & tests (included in Pro!)
- Gemini CLI: Large analysis (free)

**Why this works:**
Codex is included in ChatGPT Pro but many people don't use it. By delegating the heavy coding work to Codex, you save on Claude costs while still using Claude for the parts it's best at (reasoning, design decisions).

Built an open-source CLI that automates this workflow:
https://github.com/AI-Driven-School/claude-codex-collab

One command generates requirements → design → code → tests → review.

Anyone else experimenting with multi-AI workflows?
```

---

## 投稿のコツ

1. **タイミング**: 米国時間の朝9-11時（日本時間22-24時）
2. **コメント対応**: 投稿後1-2時間は返信できるように
3. **自己宣伝ルール**: 各subredditの規約を確認
4. **画像**: promo.gif を投稿に含める（可能な場合）

---

## 投稿URL

投稿後、URLをここに記録:

- r/ClaudeAI:
- r/SideProject:
- r/ChatGPT:
