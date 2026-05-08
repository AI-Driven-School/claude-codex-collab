# Stage 2 vs PR-Agent 直接比較レポート

> 実行日: 2026-05-08
> 結論: **同条件直接比較は不可能**。土俵が異なる。

## 検証手順

1. PR-Agent (qodo-ai) を pip install
2. CLI 仕様確認: `pr-agent --pr_url=<URL> review` → **GitHub PR URL 必須**
3. Prompt 内部仕様: PR diff (`__new hunk__` / `__old hunk__` 形式、`+`/`-` prefix) を前提
4. → Stage 2 の自然言語主張は入力できない

## 確認した PR-Agent の design

PR-Agent は `pr-agent v0.2.4` (PyPI) / `v0.32` (GitHub) のいずれでも:
- 入力: GitHub/GitLab/Bitbucket PR URL or local diff
- 内部 prompt: `pr_reviewer_prompts.toml` で「diff の `+` 行に対して review コメント」を生成
- 自然言語の論述・事業判断・法務主張は**評価対象外**

## 「比較不可能」の意味

| 観点 | 本 /debate stack | PR-Agent |
|---|---|---|
| 入力 | 自然言語主張 (claim file) | git PR diff |
| 評価対象 | 主張の論理的正しさ・事実誤認 | コード変更の品質・バグ・最適化 |
| 出力 | verdict (fatal/partial/sound) + 反論ポイント | line-level コメント + 改善提案 |
| Multi-agent | Solver / Proposer / Critic / Checker (3社+WebSearch) | 単独LLM (GPT/Claude/Gemini いずれか) |
| 用途 | 事業判断・設計判断・知識検証 | コードレビュー (PR mergeable性) |

これは **「自動車 vs 飛行機の燃費比較」** のような質問。同じ「燃費」という指標があっても、用途が違うので意味のある比較にならない。

## それでも比較したいなら

3つのアプローチが考えられる:

### A. PR-Agent の review prompt を流用
`pr_reviewer_prompts.toml` の system prompt を Stage 2 主張に対して流す。ただし PR-Agent prompt は diff 形式を前提としており、自然言語主張に流用すると prompt 内で「`+` 行を review せよ」という指示が破綻。**結果は意味不明になる**。

### B. Stage 2 主張を fake PR に成形
各主張を「`fix.md` という1ファイルに書いた、claim 内容を理由とする変更」として fake PR を作る。GitHub PR を実際に立てて PR-Agent をかけるには:
- Repo 1 つ用意
- 30件分の fake PR (each 1 commit)
- PR-Agent を 30回 起動
- 工数 1-2日。意味のある結果にならない可能性大。

### C. **コード変更系の主張**を Stage 3 で追加
これが正解。Stage 3 設計で「PR-Agent と土俵が共通する主張」を 10-20件混ぜる:
- 「TypeScript strict は不要、any でも品質OK」 → サンプルコード付き fake PR
- 「git push --force は安全」 → fake commit
- 「JSXで `dangerouslySetInnerHTML` は問題ない」 → コード変更
- 「DROP TABLE without WHERE は問題ない」 → migration PR

これらは PR-Agent の土俵で評価可能、かつ本 /debate stack でも論述として評価可能。両者の比較が成立する。

## 次のアクション (Stage 3)

Stage 3 の n=100 設計に **「コードPR形式の主張 20件」セクションを追加**。これらを:
1. 実 GitHub PR として作成 (sandbox repo)
2. PR-Agent で review
3. 本 /debate で並行 review
4. 同主張に対する catch rate 比較

これで初めて **「PR-Agent vs /debate v1.1」直接同条件比較**が成立する。

## 副次的発見

PR-Agent の prompt design は非常に diff-centric:
- `__new hunk__` / `__old hunk__` の構造化 input
- line number 参照前提
- YAML 出力強制

これは自然言語論述レビュー (本 /debate の主用途) には不向きで、逆に言えば **本 /debate の存在価値が確認できた**: PR-Agent や Greptile は「コード変更の品質」を測る道具、本 /debate は「主張・判断の正しさ」を測る道具。**競合ではなく補完**。

## 公開文書での扱い

claude-codex-collab (aiki) repo の比較セクションでは:
- 「PR-Agent との直接比較は土俵が違うため Stage 2 では不可能」
- 「Stage 3 で **コード変更系主張 20件** を追加し、PR-Agent と /debate の同条件比較を行う」
- 「現状は ‘事業判断検証’ 領域での独自性として位置づけ」

を honest に書く。誇張も矮小化もしない。

## 参考: Greptile / Qodo Merge / CodeRabbit も同じ

| ツール | 用途 | 直接比較可能性 |
|---|---|:-:|
| PR-Agent (OSS) | PR diff review | ✗ 同上 |
| Greptile (商用 82%) | PR + repo-wide review | ✗ 同上 |
| Qodo Merge (商用) | PR review (multi-agent) | ✗ 同上 |
| CodeRabbit (商用) | PR comment review | ✗ 同上 |
| **本 /debate v1.1** | **自然言語主張 / 事業判断 / 知識検証** | — (独自カテゴリ) |

→ 商用ベンチで報告される「82%」「44%」等は **すべて PR diff の bug catch rate** であり、本 /debate の主張 catch rate と直接比較すると**ジャンル違い**。

## 修正すべき過去記述

`benchmarks/stage1-debate-catch-rate.md` および `stage2-debate-n30.md` で「Greptile (commercial best) 82% を上回る」と書いた箇所は **正確には「PR diff レビューの数値であって、本 /debate と土俵が違う」** を補足すべき。
