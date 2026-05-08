# Stage 2 独立採点結果

> 実行日: 2026-05-08
> 採点者A (self): Solver Claude Opus 4.7 (this) — bench を運用した本人
> 採点者B (independent): Agent (general-purpose, separate context Claude session) — 完全な fresh context、bundleファイルのみ参照

## TL;DR

**Recall 100% が採点者を変えても確認された。** verdict の精緻分類では一部不一致 (κ=0.534) だが、最終 recall は不変。

| Metric | Self grading | Independent grading |
|---|:-:|:-:|
| Recall (False caught) | **100%** (18/18) | **100%** (18/18) ✓ |
| True kept (Precision proxy) | 0% (0/5) | 0% (0/5) |
| Verdict classification agreement | — | 72% (43/60) |
| Cohen's κ (Gemini classifications) | — | **0.576** (moderate) |
| Cohen's κ (Codex classifications) | — | 0.138 (slight) |
| Cohen's κ (combined) | — | **0.534** (moderate) |

## 主な不一致パターン

### Self が `unclear` → Independent が `partial` (12件)

私の抽出ロジック（`is誤り` `は不正確` を順にチェック）は Codex の婉曲表現「概ね正しい、ただし条件あり」を `unclear` と分類してしまった。Independent grader は同じ表現を `partial` と分類。

→ **Codex の応答スタイル「sound + qualification」を`partial`と分類するのが正しい**。Self の抽出ロジックには改善余地あり。

### G5/G6/G7 で Gemini 分類が割れる

Independent grader 注記:「G5/G6/G7 は API rate-limit error dump で実質 rebuttal なし」と判定。Self は通常分類。

→ Gemini API 末尾でレート制限の dump を拾った可能性。これは Stage 3 で `--retry` ロジックが必要な箇所。

### T5 (METR Time Horizon、True claim)

- Self: Codex = `sound` (唯一の sound 判定)
- Independent: Codex = `partial`

Codex の応答「事実としては概ね正しい」を `sound` と読むか `partial` と読むかで分かれた。実際は両方の読み方が成立する境界事例。

## なぜ Recall が変わらなかったのか

False claim では:
- Gemini が `fatal` または `partial` を出せば catch
- Codex が `fatal` または `partial` を出せば catch
- どちらかひとつでも出れば最終 catch

Independent grader によれば、両 reviewer が False claim 18件全件で `partial` 以上の verdict を出している。
→ **「両 reviewer が常に何かしら反論する」傾向**は self/independent 両方が観察。
→ 結果として recall は採点者によらず 100%。

## Independent grader の傾向観察

> Independent grader の notes より:
> - Gemini: 17 fatal, 10 partial, 3 unclear
> - Codex:   1 fatal, 29 partial, 0 unclear
> - 両 reviewer とも `no_rebuttal` を一度も書かなかった
> - 純粋な `sound` も一度もなかった
> - **両 reviewer は常に何かしら反論ポイントを上げる傾向**

→ これは debate を回した時の構造的特徴。reviewer prompt が「反論しろ」と命じている以上、True claim に対しても何かしら指摘する。Stage 3 ではプロンプトを「反論できなければ明示的に sound と書け」と強化すべき。

## バイアス影響度の結論

| バイアス源 | 影響 |
|---|:-:|
| Self-evaluation | classification 一部に影響 (κ=0.534)、Recall 不変 |
| Reviewer の「常に反論する」傾向 | True claim での precision を下げる構造的問題 |
| Codex 内蔵 web_search (Checker と重複) | 影響大、Stage 3 で要対処 |

**Recall 100% は robust。Precision の数値は self/independent で同じ 0%。bias の影響は metric ではなく verdict の細分類にのみ出る。**

## Stage 3 への要件 (採点関連)

1. **採点ロジック改善**: 「概ね正しい + 条件あり」を `partial` に分類するルール明文化
2. **reviewer prompt 強化**: 「反論なければ verbatim で 'Solver主張は妥当' と書け」を再徹底
3. **Codex web_search 切離し**: Critic と Checker の独立性確保
4. **κ ≥ 0.7 を目標**: 現状 0.534 で moderate、Stage 3 では substantial agreement に
5. **complete blind grading**: 採点者に ground truth を渡さない（今回は渡していないが、明文化）

## 副次的価値

独立採点プロセス自体が **「Self-evaluation bias を測る」フレームワーク**として機能した。Stage 1/2 で「self bias 残存」と書いた留保を、定量的に「**bias は verdict 分類に影響するが metric 結論は不変**」と示せた。
