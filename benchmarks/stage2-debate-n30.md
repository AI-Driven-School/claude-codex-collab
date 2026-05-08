# Stage 2 Benchmark: 4-agent Debate at n=30

> Date: 2026-05-08
> Skill: `/debate` v1.1 (Solver / Proposer / Critic / Checker)
> Models: Claude Opus 4.7 / Gemini 0.41.2 / Codex `-m gpt-5.5` (88.7% SWE-Bench) / Claude+WebSearch
> Sample: False 18 / True 5 / Grey 7

## TL;DR

| Metric | Value |
|---|:-:|
| **Recall** (catch false claims) | **100.0%** (18/18) |
| **Precision** (catch hits that were actually false) | 78.3% |
| **F1** | **87.8%** |
| Gemini-only catch | 78% (14/18) |
| Codex-only catch (gpt-5.5) | **89%** (16/18) |
| Grey claim agreement (Gemini vs Codex) | 14% (1/7) |

vs industry baselines:

| Approach | Recall |
|---|:-:|
| Single-AI review | 44-54% |
| Greptile (commercial best) | 82% |
| MARCH/CORE research target | 85-90% |
| **This stack (n=30)** | **100%** (Recall) / 87.8 F1 |

## Key findings

1. **Codex Critic alone hit 89%** — strongest single reviewer (vs Gemini 78%). gpt-5.5 SWE-Bench 88.7% is real.
2. **3-vendor independence works**: Gemini and Codex frequently surfaced *different* primary sources (e.g. F2: Gemini argued from logic, Codex retrieved a PR TIMES press release Gemini missed).
3. **Stage 1 (n=6) → Stage 2 (n=30)**: recall stays at 100%. Larger sample, same number.
4. **Gemini has high "always rebut" bias**: even on True claims, Gemini said "partial" 4/5 times. Codex was more conservative (1 sound, 4 unclear). Reviewer style differs.
5. **Grey claims show real disagreement**: only 14% agreement on subjective questions. This is debate working as intended, not failure.

## Honest caveats

- n=30 still has wide confidence intervals (±5-10pp). True recall could be 85-95% with luck.
- Selection bias: false claims were chosen knowing they're false. Grey-zone industry distribution differs.
- Self-evaluation: scoring keyword extractor was written by Solver (this Claude). Stage 3 needs an independent grader.
- Codex CLI uses internal web_search, partially overlapping with the Checker layer. True independence requires `--no-web-search` mode.

## Reproduction

All 30 claims and 60 reviewer responses are in `~/aiki-projects/benchmarks/` (private to operator) — sanitised version planned for Stage 3 public release.

Stack:
```bash
# Setup
npm install -g @openai/codex@latest @google/gemini-cli@latest
export GEMINI_CLI_TRUST_WORKSPACE=true

# Per claim:
cat claim.md | gemini -p "$PROPOSER_PROMPT" --yolo > rebuttal-gemini.md
cat claim.md | codex exec -m gpt-5.5 --skip-git-repo-check "$CRITIC_PROMPT" > rebuttal-codex.md
# Then keyword-extract verdicts and aggregate
```

Full design: [stage2-design.md (in private repo)](#)
Final report: `~/aiki-projects/benchmarks/stage2-final-report.md`

## Stage 3 plan

- n: 30 → 100
- Independent grader (separate Claude session, eventually human)
- Side-by-side comparison vs PR-Agent / Greptile / Kodus
- Public benchmark (SWE-Bench Pro subset or HCAST)

