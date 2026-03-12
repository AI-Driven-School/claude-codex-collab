# 設計書: ルール強制実行（Rule Enforcement）

## 概要

Claudeが委譲ルールを無視してEdit/Writeを実行することを、PreToolUse hookの`exit 2`でハードブロックする。

## アーキテクチャ

```
UserPromptSubmit                    PreToolUse (Edit|Write)
┌─────────────────┐                ┌──────────────────────┐
│ agent-router.sh  │──state file──→│ enforce-delegation.sh │
│ (検知・記録)      │               │ (判定・ブロック)       │
└─────────────────┘                └──────────────────────┘
        │                                    │
        ▼                                    ▼
  .claude/.routing_context            exit 0 (許可)
  (実装タスク検知フラグ)               exit 2 (ブロック)
```

## 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/hooks/enforce-delegation.sh` | **新規**: Edit/Write前のハードブロックhook |
| `.claude/hooks/agent-router.sh` | **修正**: 検知結果を状態ファイルに書き出す |
| `.claude/settings.json` | **修正**: suggest-codex → enforce-delegationに差し替え |
| `CLAUDE.md` | **修正**: 強制ルールセクション追加 |

## コンポーネント詳細

### 1. enforce-delegation.sh（新規）

PreToolUse (Edit|Write) で実行される判定hook。

#### 判定フロー

```
入力: CLAUDE_TOOL_INPUT (JSON: file_path, content等)
  │
  ├─ エスケープハッチ: FORCE_CLAUDE=1 → exit 0 (許可)
  │
  ├─ ホワイトリスト判定
  │   ├─ 設定ファイル (.json, .yaml, .toml) → exit 0
  │   ├─ ドキュメント (.md) → exit 0
  │   ├─ メタファイル (CLAUDE.md, AGENTS.md等) → exit 0
  │   └─ docs/, .claude/, .codex/, .gemini/, .grok/ 配下 → exit 0
  │
  ├─ パイプライン違反チェック
  │   └─ .pipeline_phase = implement|test → exit 2 (Codex担当)
  │
  ├─ ルーティングコンテキスト確認
  │   └─ .routing_context に impl_detected=true → exit 2
  │
  ├─ セッション編集カウント
  │   ├─ .session_new_files >= 3 → exit 2
  │   └─ .session_edit_files >= 5 → exit 2 (警告→次回ブロック)
  │
  └─ デフォルト → exit 0 (許可)
```

#### ブロックメッセージ例

```
🚫 BLOCKED: Implementation task should be delegated to Codex.

Reason: Large-scale implementation detected (5+ file edits in session).

To proceed:
  1. Run `/implement` to delegate to Codex ($0)
  2. Or set FORCE_CLAUDE=1 to override:
     export FORCE_CLAUDE=1
```

#### セッションカウンター

- `.claude/.session_edit_count`: 編集ファイル数（ユニーク）
- `.claude/.session_new_files`: 新規作成ファイル数
- リセット: ユーザーが`/project`完了時、または手動で`rm .claude/.session_*`

### 2. agent-router.sh（修正）

#### 追加: ルーティングコンテキスト書き出し

```bash
# 実装タスク検知時に状態ファイルを作成
ROUTING_CTX="${PROJECT_DIR}/.claude/.routing_context"

if echo "$input_lower" | grep -qiE "$codex_keywords"; then
    echo "impl_detected=true" > "$ROUTING_CTX"
    echo "detected_at=$(date +%s)" >> "$ROUTING_CTX"
else
    # 実装以外のプロンプトではコンテキストをクリア
    rm -f "$ROUTING_CTX"
fi
```

### 3. settings.json（修正）

```json
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-delegation.sh"
        }
      ]
    }
  ]
}
```

`suggest-codex.sh`を`enforce-delegation.sh`に**置き換える**（併存不要）。

### 4. CLAUDE.md（修正）

追加するセクション:

```markdown
## Rule Enforcement (MANDATORY)

### HARD RULES - These are NOT suggestions

1. **NEVER implement code directly** when the task matches Codex delegation criteria:
   - 3+ new files → MUST delegate to Codex via `/implement`
   - 10+ file changes → MUST delegate to Codex
   - Test file creation → MUST delegate to Codex
   - These rules are enforced by hooks. Attempting to Edit/Write will be BLOCKED.

2. **NEVER start implementation without design artifacts**:
   - `docs/requirements/{feature}.md` MUST exist before coding
   - `docs/specs/{feature}.md` MUST exist before coding
   - Use `/requirements` and `/spec` to create them first

3. **Override**: User can set `export FORCE_CLAUDE=1` to bypass all blocks.
   This is the ONLY way to override. Do NOT suggest workarounds.
```

## ファイルホワイトリスト詳細

| パターン | 理由 |
|---------|------|
| `*.md` | ドキュメント・設計書はClaude担当 |
| `*.json`, `*.yaml`, `*.yml`, `*.toml` | 設定ファイルは小規模変更 |
| `docs/**` | 設計成果物 |
| `.claude/**`, `.codex/**`, `.gemini/**`, `.grok/**` | メタ設定 |
| `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `GROK.md` | エージェント設定 |
| `skills/**` | スキル定義 |
| `scripts/**/*.sh` | hookスクリプト自体の編集 |
| `tasks/**` | タスク管理 |

## エスケープハッチ

```bash
# 一時的にブロック解除
export FORCE_CLAUDE=1

# セッションカウンターリセット
rm -f .claude/.session_edit_count .claude/.session_new_files

# ルーティングコンテキストクリア
rm -f .claude/.routing_context
```

## 状態遷移

| 状態 | トリガー | 遷移先 |
|------|---------|--------|
| 通常 | 実装キーワード入力 | impl_detected |
| impl_detected | Edit/Write試行 | BLOCKED (exit 2) |
| impl_detected | 非実装プロンプト | 通常 (コンテキストクリア) |
| BLOCKED | FORCE_CLAUDE=1 | 通常 (バイパス) |
| BLOCKED | `/implement`実行 | Codex委譲 |
| パイプライン中 | implement phase Edit | BLOCKED |
| パイプライン中 | design phase Edit | 許可 |
