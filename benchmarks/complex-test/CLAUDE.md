# CLAUDE.md - Claude Code 自動設定

このファイルはClaude Codeが自動的に読み込み、プロジェクト固有のルールを適用します。

## プロジェクト概要

**StressAgent Pro** - AI駆動型メンタルヘルスSaaS
- バックエンド: FastAPI (Python)
- フロントエンド: Next.js (TypeScript)
- DB: PostgreSQL

## 自動タスク委譲ルール

### Codexへの自動委譲

以下のタスクは **自動的にCodexに委譲** してください：

1. **コードレビュー**
   - トリガー: 「レビュー」「review」「チェックして」
   - コマンド: `codex review --uncommitted`

2. **ユニットテスト作成**
   - トリガー: 「テスト作成」「test」「テストを書いて」
   - コマンド: `codex exec --full-auto "指定ファイルのユニットテストを作成"`

3. **ドキュメント生成**
   - トリガー: 「ドキュメント」「README」「説明を書いて」
   - コマンド: `codex exec --full-auto "ドキュメントを生成"`

4. **定型リファクタリング**
   - トリガー: 「リファクタ」「整理して」「きれいにして」
   - コマンド: `codex exec --full-auto "コードを整理"`

### 委譲の実行方法

```bash
# バックグラウンドで実行
codex exec --full-auto -C /Users/yu01/Desktop/StressAIAgent "タスク内容" &

# 結果確認
codex review --uncommitted  # レビューの場合
```

## サブエージェント活用ルール

### 必須: 以下の場合はTaskツールでサブエージェントを起動

1. **コード探索 (Explore)**
   - 「〜はどこ？」「〜を探して」「構造を教えて」
   - `subagent_type: Explore`

2. **計画立案 (Plan)**
   - 「〜を実装したい」「設計して」「計画を立てて」
   - `subagent_type: Plan`

3. **並列調査**
   - 複数ファイル/機能の調査が必要な場合
   - 複数のTaskを並列起動

### サブエージェント起動例

```
Task(subagent_type="Explore", prompt="認証機能の実装箇所を調査")
Task(subagent_type="Plan", prompt="Teams連携の実装計画を立案")
```

## 自動ワークフロー

### 新機能実装時

```
1. [Plan] 設計・計画（サブエージェント）
2. [Claude Code] 実装
3. [Codex] コードレビュー（自動委譲）
4. [Claude Code] レビュー指摘の修正
5. [Codex] テスト作成（自動委譲）
6. [Claude Code] 最終確認・コミット
```

### バグ修正時

```
1. [Explore] 原因調査（サブエージェント）
2. [Claude Code] 修正実装
3. [Codex] レビュー（自動委譲）
4. [Claude Code] コミット
```

## コマンドリファレンス

### Codex委譲コマンド

```bash
# コードレビュー
codex review --uncommitted

# 特定ブランチとの差分レビュー
codex review --base main

# 非同期タスク実行
codex exec --full-auto "タスク内容"

# 特定ディレクトリで実行
codex exec --full-auto -C /path/to/dir "タスク内容"
```

### よく使うパス

- バックエンド: `backend/app/`
- フロントエンド: `frontend/app/`, `frontend/lib/`
- テスト: `tests/`, `backend/tests/`
- 設定: `backend/.env`, `frontend/.env.local`

## 品質基準

- TypeScript: 型エラーなし
- Python: flake8/black準拠
- テストカバレッジ: 主要機能は必須
- セキュリティ: 認証必須エンドポイントの確認

## 禁止事項

- 本番環境の認証情報をコードに含めない
- `--force` 付きのgit pushは確認なしで実行しない
- DBの破壊的変更は必ず確認を取る

---

## 🤖 自動実行ルール（重要）

Claude Codeは以下のルールに従って **自動的に** Codexとサブエージェントを活用すること。

### 1. キーワード検出時の自動委譲

| ユーザーの発言に含まれるキーワード | 自動アクション |
|--------------------------------|--------------|
| 「レビュー」「review」「チェックして」 | `./scripts/auto-delegate.sh review` |
| 「テスト作成」「test書いて」 | `./scripts/auto-delegate.sh test` |
| 「ドキュメント」「README」 | `./scripts/auto-delegate.sh docs` |
| 「リファクタ」「整理して」 | `./scripts/auto-delegate.sh refactor` |

### 2. サブエージェント自動起動

| 状況 | 起動するサブエージェント |
|-----|----------------------|
| コードベースの調査が必要 | `Task(subagent_type="Explore")` |
| 実装計画が必要 | `Task(subagent_type="Plan")` |
| 複数ファイルの並列調査 | 複数の `Task(subagent_type="Explore")` を並列 |
| バックグラウンドでの長時間タスク | `Task(run_in_background=true)` |

### 3. 実装フロー（必須）

新機能・修正を行う際は、以下のフローを **自動的に** 実行：

```
[ユーザー依頼]
    ↓
[1] Task(Explore) で関連コードを調査 ← 自動
    ↓
[2] 実装を行う
    ↓
[3] ./scripts/auto-delegate.sh review ← 自動でCodexレビュー
    ↓
[4] レビュー指摘があれば修正
    ↓
[5] 完了報告
```

### 4. 並列実行の活用

独立したタスクは **必ず並列で** 実行：

```python
# 良い例: 並列で調査
Task(subagent_type="Explore", prompt="認証機能を調査")
Task(subagent_type="Explore", prompt="DB構造を調査")  # 同時に実行

# 悪い例: 順番に実行（非効率）
# Task → 結果待ち → Task → 結果待ち
```

### 5. 自動委譲スクリプト

```bash
# コードレビュー（最も頻繁に使用）
./scripts/auto-delegate.sh review

# テスト作成
./scripts/auto-delegate.sh test backend/app/services/teams_service.py

# ドキュメント生成
./scripts/auto-delegate.sh docs

# カスタムタスク
./scripts/auto-delegate.sh custom "〇〇を実装して"

# バックグラウンド実行（長時間タスク）
./scripts/auto-delegate.sh background "全ファイルのリファクタリング"
```

### 6. 結果の確認

Codex実行後は必ず結果を確認し、ユーザーに報告：

```bash
# 最新の出力を確認
cat .codex-tasks/output-*.txt | tail -100
```
