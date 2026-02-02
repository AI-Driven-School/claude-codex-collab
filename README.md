# 3AI協調開発テンプレート

Claude Code + Codex + Gemini CLI の3つのAIで開発タスクを最適分担。
コスト削減と効率化を両立。

| AI | 担当 | 強み |
|----|------|------|
| **Claude Code** | 設計・実装 | 最高の推論能力 |
| **Codex** | テスト・レビュー | 高速・自動化 |
| **Gemini** | 解析・リサーチ | 1Mトークン・無料枠 |

---

## コスト効果

| タスク | Claude単独 | 3AI分担 | 削減 |
|-------|-----------|---------|------|
| 機能追加 | 80,000 | 15,000 | **-81%** |
| リファクタ | 50,000 | 0 | **-100%** (Gemini無料) |
| リサーチ | 30,000 | 0 | **-100%** (Gemini無料) |

---

## インストール

```bash
curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install-fullstack.sh | bash -s -- my-app
```

3つのAIツールが未インストールの場合、自動でインストールされます。

---

## 使い方

### Claude Code（設計・実装）

```bash
/feature ユーザー認証    # 機能追加
/fix ログインエラー      # バグ修正
/ui ログインフォーム     # UI生成
/deploy                  # デプロイ
```

### Codex（テスト・レビュー）

```bash
/review                  # コードレビュー
/test src/components/    # テスト生成
```

### Gemini（解析・リサーチ）

```bash
/analyze                 # コードベース解析
/research "Next.js 15"   # 技術リサーチ
/refactor src/lib/       # リファクタ提案
```

---

## 分担フロー

```
/feature ユーザー認証

[設計] → [UI] → [実装] → [テスト] → [レビュー] → [デプロイ]
Claude   Claude  Claude   Codex     Codex      Claude
```

```
/refactor src/

[解析] → [提案] → [実装] → [レビュー]
Gemini   Gemini   Claude   Codex
```

---

## コマンド一覧

| コマンド | 説明 | 担当AI |
|---------|------|--------|
| `/feature <名前>` | 機能追加 | Claude → Codex |
| `/fix <内容>` | バグ修正 | Claude → Codex |
| `/ui <名前>` | UI生成 | Claude |
| `/deploy` | デプロイ | Claude |
| `/review` | コードレビュー | Codex |
| `/test <path>` | テスト生成 | Codex |
| `/analyze` | コード解析 | Gemini |
| `/research <質問>` | リサーチ | Gemini |
| `/refactor <path>` | リファクタ提案 | Gemini |

---

## 動作環境

- macOS / Linux / WSL2
- Node.js 18+
- Claude Code (`npm i -g @anthropic-ai/claude-code`)
- Codex (`npm i -g @openai/codex`)
- Gemini CLI (`npm i -g @google/gemini-cli`)

---

MIT License | [最小構成版](https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install.sh) | [Issue](https://github.com/yu010101/claude-codex-collab/issues)
