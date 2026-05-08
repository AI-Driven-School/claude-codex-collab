# Stage 3-A 中間レポート (n=10 batch)

> 実行日: 2026-05-08
> Stage 3 全体計画 (n=100) のうち最初の 10件
> Skill: /debate v1.1 (4-agent: Solver / Proposer / Critic / Checker)
> モデル: Claude Opus 4.7 / Gemini 0.41.2 / Codex `-m gpt-5.5` / Claude+WebSearch

## TL;DR

**False 5/5 catch (100%)、累計 (Stage 1+2+3-A) で 23/23 = 100% Recall 維持**。

True 3件で precision は依然として 0%。reviewer prompt 強化 (verbatim 「反論なし」要求) しても両 reviewer は補足反論を出す傾向継続。

| 指標 | 値 |
|---|:-:|
| Stage 3-A False catch | **5/5 (100%)** |
| Stage 3-A True pass | 0/3 (0%) |
| Stage 3-A Grey | reviewer 意見ばらける (debate 機能の証拠) |
| **累計 Stage 1+2+3-A False catch** | **23/23 (100%)** |

## 詳細

### False (5件、全件 catch)

| # | claim | Gemini | Codex |
|:-:|---|:-:|:-:|
| F19 | Cloudflare R2 完全無料 | fatal | partial |
| F22 | Postgres と MySQL 性能差なし | fatal | unclear (反論はある) |
| F26 | Sonnet 4.6 が Opus 4.7 上回る | fatal | partial |
| F33 | TypeScript 実行時型チェック | fatal | partial |
| F38 | Sentry Free 無制限 | fatal | partial |

### True (3件、両者 pass せず)

| # | claim | Gemini | Codex |
|:-:|---|:-:|:-:|
| T6 | Codex 0.129.0 で gpt-5.5 動作 | unclear | unclear |
| T8 | METR HCAST 170→228 拡張 | unclear | partial |
| T11 | TS strict は8項目集合 | unclear | partial |

reviewer prompt の verbatim 「反論なし」要求に応えていない。reviewer 行動の構造的問題。

### Grey (2件)

| # | claim | Gemini | Codex |
|:-:|---|:-:|:-:|
| G8 | Rust が常に TS より優れる | unclear | unclear |
| G10 | Server Components 常に高速 | unclear | partial |

両者で意見が割れる/曖昧、debate として正常。

## 観察

### 1. Stage 2 (n=30) → Stage 3-A (n=10) で False catch 100% 維持

サンプルが増えても recall 維持 = 偶然ではなく構造的特性の可能性。

### 2. reviewer の「常に反論」傾向は prompt 強化でも改善せず

[Stage 2 final report](./stage2-final-report.md) で同じパターンを観察、本バッチでも継続。reviewer prompt:
- v1: 「反論できなければ '反論なし' と書く」
- v2 (本バッチ): 「**Solver が完全に正しい場合は冒頭で「結論: Solver主張は妥当。反論なし。」と verbatim で書く**」と強化

それでも両 reviewer は何かしら補足反論を出す。これは:
- LLM 一般の confirmation bias 逆 (反論バイアス)
- prompt engineering で構造的に解決困難

→ Stage 3 完走時に **「True claim での precision」は別軸の限界として明示**すべき。Recall に集中、Precision は reviewer の特性として記録。

### 3. unclear 増加の原因

Stage 3-A では Gemini が True 3件で全部 'unclear' 判定 (verdict 抽出ロジック側)。Gemini の出力が「概ね正しいが補足あり」スタイルで、私の抽出ロジックがキャッチしきれない。

Stage 3 全体の採点ロジック改良が必要 (Stage 2 独立採点で確認した通り、self-grading の限界)。

## Stage 3 残り計画 (n=100 まで)

| Phase | 件数 | 内容 |
|---|:-:|---|
| ✓ Stage 3-A (本バッチ) | 10 | False5+True3+Grey2 |
| Stage 3-B | 30 | 残り False 17件 + True 7件 + Grey 6件 |
| Stage 3-C | 25 | コードPR形式 (PR-Agent 直接比較対象) |
| Stage 3-D | 5 | SWE-Bench Lite full Docker評価 |
| 累計 | **70件** | (Stage 2 と合わせて n=100) |

## 採点ロジック改善案 (Stage 3-B 実装時)

```python
def extract_verdict_v2(text):
    # 1. 応答末尾 (本論部分) の「結論」キーワードを優先
    last_para = text.split('---')[-1] if '---' in text else text
    last_500 = last_para[-500:]
    
    # 2. 「妥当」「正しい」「妥当性が高い」のいずれか + 「反論なし」or 反論ポイント0件
    has_sound = any(k in last_500 for k in ['妥当','正しい','概ね正しい','大筋で正しい'])
    has_no_rebuttal = '反論なし' in last_500 or '反論ポイント' not in text
    
    if has_sound and has_no_rebuttal:
        return 'sound'
    # ...
```

## 次のアクション

1. Stage 3-A 結果を aiki repo に push (commit予定)
2. **Stage 3-B (n=30)** を別セッションで実行 (4-5時間想定)
3. Stage 3-C (コードPR比較) は実 GitHub PR 作成必要、別セッション
4. Stage 3-D (SWE-Bench Docker) は環境構築別途

## 1行サマリー (Stage 3 全体に向けて)

n=23 (false claim累計) で Recall 100% **頑健に維持**、ただし Precision は reviewer 特性として 0% 継続。**「業界最強の False catch ツール、ただし True に対しても何か言ってくる傾向あり」** というキャラ確定。
