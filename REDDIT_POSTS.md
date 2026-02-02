# Reddit 投稿原稿

---

## r/ClaudeAI 向け

### Title
```
I made Claude Code work smarter by delegating implementation to Codex - 75% cost reduction
```

### Body
```
I was frustrated with Claude Code costs. It's great at reasoning and design decisions, but having it write boilerplate CRUD code felt wasteful.

So I built a simple workflow that delegates tasks based on each AI's strengths:

| AI | Role | Cost |
|---|---|---|
| Claude | Design, decisions, code review | Pay per use |
| Codex | Implementation, tests | $0 (included in ChatGPT Pro) |
| Gemini | Large codebase analysis | Free |

**How it works:**

```
/project user-auth

[1/6] Requirements  → Claude generates spec
[2/6] API Design    → Claude creates OpenAPI spec
[3/6] Implementation → Codex builds it ($0)
[4/6] Tests         → Codex generates tests ($0)
[5/6] Review        → Claude reviews the code
[6/6] Deploy        → Ship when approved
```

Each phase has approval/rejection, so you stay in control.

**Why I like it:**

- Claude only does what it's best at (thinking)
- Codex handles the grunt work (free with ChatGPT Pro)
- You get design docs for everything, even as a solo dev
- Having Claude review Codex's work feels safer than trusting one AI completely

**Real example:**

I added an "Organization Analytics" feature to a SaaS I'm building. The workflow generated:
- Requirements doc
- OpenAPI spec
- UI mockup spec
- Backend API
- Frontend dashboard
- 10 E2E tests
- Code review doc

All from one command.

**GitHub:** https://github.com/AI-Driven-School/claude-codex-collab

It's MIT licensed, free to use. Would appreciate feedback on the approach or suggestions for improvement.

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
I made a CLI that makes Claude + Codex work together - cuts my AI costs by 75%
```

### Body
```
As a solo dev, I was spending too much on AI coding tools. Claude Code is amazing for design decisions, but using it for everything adds up.

**The problem:**

Claude thinks carefully about everything. That's great for architecture decisions, but overkill for writing a simple API endpoint.

**My solution:**

I built a workflow where:
- Claude handles design and review (the thinking parts)
- Codex handles implementation (the typing parts) - free with ChatGPT Pro
- Gemini handles large codebase analysis - also free

**One command does everything:**

```
/project user-auth

[1/6] Requirements → Claude
[2/6] Design → Claude
[3/6] Implementation → Codex ($0)
[4/6] Tests → Codex ($0)
[5/6] Review → Claude
[6/6] Deploy → approve & ship
```

**What I like about it:**

1. **Cost effective** - 75% cheaper than Claude-only
2. **Documentation** - Every feature gets requirements, API specs, UI specs automatically
3. **Trust** - Having one AI review another's work feels safer

**Real world test:**

Built an analytics dashboard feature for my SaaS. Generated 7 docs and 10 test cases automatically.

**GitHub:** https://github.com/AI-Driven-School/claude-codex-collab

Free and MIT licensed. Happy to answer questions about the implementation.
```

### Flair
```
Built with AI / Open Source
```

---

## r/LocalLLaMA / r/OpenAI 向け

### Title
```
Using Codex (ChatGPT Pro) for implementation while Claude handles design - my multi-AI dev workflow
```

### Body
```
Found a way to get more value from ChatGPT Pro subscription by using Codex alongside Claude.

**The setup:**

| Task | AI | Why |
|------|-----|-----|
| Requirements, design | Claude | Better at reasoning |
| Implementation | Codex | Fast, $0 with Pro |
| Testing | Codex | Consistent with impl |
| Code review | Claude | Catches issues |
| Large analysis | Gemini | 1M token context, free |

**Why this works:**

Codex is included in ChatGPT Pro but underutilized. By having Claude generate specs first, then Codex implement them, you get:
- Claude's reasoning for the hard decisions
- Codex's speed for the actual coding
- Cost savings (implementation is usually the most tokens)

**I built an OSS tool to automate this:**

https://github.com/AI-Driven-School/claude-codex-collab

One command runs the full workflow with approval gates at each step.

Anyone else doing multi-AI development? Curious what combinations work for you.
```

---

## r/webdev 向け

### Title
```
Made a CLI that delegates frontend/backend work between Claude and Codex automatically
```

### Body
```
Built a tool to solve a personal annoyance: Claude Code is great but expensive for routine coding.

**What it does:**

When you run `/project <feature-name>`, it:

1. Has Claude write requirements and API specs
2. Delegates implementation to Codex (free with ChatGPT Pro)
3. Has Codex generate tests
4. Has Claude review the code against the original specs
5. Deploys when you approve

**Tech stack it generates:**
- FastAPI backend
- Next.js 14 frontend
- Playwright E2E tests
- OpenAPI specs

**Why I made it:**

As a solo dev, I never wrote docs for my own projects. Now every feature automatically gets:
- Requirements doc
- API spec (OpenAPI/YAML)
- UI spec
- Code review doc

Having documentation makes it way easier to onboard collaborators or remember what I built 6 months later.

**Link:** https://github.com/AI-Driven-School/claude-codex-collab

Free, MIT licensed. Feedback welcome.
```

---

## 投稿のコツ

1. **タイミング**: 米国時間の朝9-11時（日本時間22-24時）が最もアクティブ
2. **コメント対応**: 投稿後1-2時間は返信できるように
3. **謙虚なトーン**: 「I made this」「solved my problem」「happy to get feedback」
4. **宣伝感を消す**: 「sharing because it helped me」というスタンス
5. **質問で終わる**: 「Anyone else doing X?」でエンゲージメント促進

---

## 投稿URL（記録用）

投稿後、URLをここに記録:

- r/ClaudeAI:
- r/SideProject:
- r/LocalLLaMA:
- r/OpenAI:
- r/webdev:

---

## Awesome List PR 用

### awesome-claude-code への PR

```markdown
## Multi-AI Workflows

- [claude-codex-collab](https://github.com/AI-Driven-School/claude-codex-collab) - Orchestrates Claude (design/review), Codex (implementation), and Gemini (analysis) for cost-effective development workflows. Includes approval gates and automatic documentation generation.
```

### 送信先

- `awesome-claude`
- `awesome-chatgpt`
- `awesome-ai-tools`
