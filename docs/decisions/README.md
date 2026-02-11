# Architecture Decision Records (ADR)

このディレクトリには、プロジェクトの重要な決定事項を記録します。

## Why

- Claudeは会話終了時に記憶をリセットする
- 重要な決定をファイルに残すことで、次回セッションでも文脈を維持できる
- チームメンバー（人間・AI問わず）が「なぜこの決定をしたか」を追跡できる

## Format

ファイル名: `YYYY-MM-DD-title.md`

```markdown
# タイトル

## Status
Accepted / Proposed / Deprecated / Superseded

## Context
なぜこの決定が必要だったか

## Decision
何を決定したか

## Consequences
この決定による影響（良い点・悪い点）
```

## Example

```
docs/decisions/
├── 2025-01-15-use-nextjs-app-router.md
├── 2025-01-20-adopt-shadcn-ui.md
└── 2025-02-01-3ai-workflow.md
```

## How to Use

Claudeに対して：
- 「この決定を記録して」
- 「なぜXXXを選んだか記録して」
- 「今の議論をADRにして」

と依頼すると、このディレクトリに記録します。
