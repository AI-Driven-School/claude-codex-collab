# 要件定義: ルール強制実行（Rule Enforcement）

## ユーザーストーリー

AS A ソロ開発者（4-AI協調ワークフロー利用者）
I WANT TO Claudeがrulesの委譲ルールを無視して自分で実装することをハードブロックしたい
SO THAT 各AIの役割分担が確実に守られ、コスト最適化とワークフロー一貫性が保たれる

## 背景・問題

現状のHookは全て`exit 0`で終了しており、提案（Advisory）止まり。
Claudeは提案を表示した上で無視し、自分でEdit/Writeを実行してしまう。

### 具体的な違反パターン

1. **実装の直接実行**: Codexに委譲すべき大規模実装をClaudeが直接Edit/Writeする
2. **設計書なしの着手**: requirements/specを作らずにコードを書き始める
3. **提案の無視**: Hook提案（Codex/Gemini/Grok委譲）を表示後も自分で処理する

## 受入条件

### 機能要件

- [ ] PreToolUse(Edit|Write)フックが、実装タスク検知時に`exit 2`でブロックする
- [ ] ブロック時に「なぜブロックされたか」「何をすべきか」を明示するメッセージを出力する
- [ ] `/project`パイプライン実行中（`.claude/.pipeline_phase`存在時）はphaseに応じて適切にブロック/許可する
- [ ] 設計書（requirements/specs）が存在しない機能の実装をブロックする
- [ ] CLAUDE.mdに強制的な委譲ルールを追加し、Claude自身が内部的にもルールを遵守する
- [ ] ユーザーが明示的にオーバーライドできるエスケープハッチを用意する（`FORCE_CLAUDE=1`等）

### 非機能要件

- パフォーマンス: Hook実行は200ms以内
- 互換性: 既存のpost-impl-checkフックと競合しない
- 保守性: ブロック条件の追加・変更が容易

## ブロック判定ロジック

### ブロックする条件（AND/OR）

1. **大規模変更検知**: 直近セッションで5ファイル以上のEdit/Writeを試行
2. **新規ファイル作成**: 3ファイル以上の新規Write
3. **パイプライン違反**: `.pipeline_phase`がimplement/testなのにClaudeがEdit
4. **設計書未作成**: 実装キーワード検知後、対応するrequirements/specsが未作成

### ブロックしない条件（ホワイトリスト）

1. `FORCE_CLAUDE=1` 環境変数が設定されている
2. 設定ファイル編集（`.json`, `.yaml`, `.toml`, `.md`のみ）
3. CLAUDE.md/AGENTS.md等のメタファイル編集
4. `/project`パイプラインのdesign/review phaseでの編集
5. 5行以下の小規模修正

## 制約事項

- Claude Code Hooks仕様に準拠（exit 0=許可, exit 2=ブロック）
- 既存の`.claude/settings.json`構造を維持
- bash scriptのみで実装（外部依存なし）
