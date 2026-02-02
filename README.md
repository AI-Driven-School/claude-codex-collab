# 3AI協調開発テンプレート v5.0

要件定義から本番デプロイまで、**承認フロー付き**で完全自動化。
CLIだけで設計書・モックアップ・実装・テストを一貫管理。

```
/project ユーザー認証

[1/8] 要件定義を生成しました → docs/requirements/auth.md
      承認しますか？ [Y/n/edit]
```

---

## 開発フロー

```
/project <機能名>
    ↓
[1] 要件定義   → 承認待ち → docs/requirements/
[2] 画面設計   → 承認待ち → docs/specs/ + mockups/
[3] API設計    → 承認待ち → docs/api/
[4] DB設計     → 承認待ち → migrations/
[5] 実装       → 自動     → src/
[6] テスト     → 自動     → tests/  (Codex)
[7] レビュー   → 自動     → docs/reviews/  (Codex)
[8] デプロイ   → 承認待ち
```

**人間が判断**: 要件・設計・デプロイ
**AIに任せる**: 実装・テスト・レビュー

---

## 3AI分担

| AI | 担当 | フェーズ |
|----|------|---------|
| **Claude Code** | 設計・実装 | 要件定義、画面設計、API設計、DB設計、実装 |
| **Codex** | 品質保証 | テスト生成、コードレビュー |
| **Gemini** | 分析・調査 | 大規模解析、リサーチ、リファクタ |

---

## インストール

```bash
curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install-fullstack.sh | bash -s -- my-app
```

---

## コマンド一覧

### プロジェクト管理

| コマンド | 説明 |
|---------|------|
| `/project <名前>` | 承認フロー付き完全ワークフロー |
| `/approve` | 現在フェーズを承認 |
| `/reject <理由>` | 却下して再生成 |
| `/status` | 進捗確認 |

### 設計フェーズ

| コマンド | 出力 |
|---------|------|
| `/requirements <機能>` | docs/requirements/*.md |
| `/spec <画面>` | docs/specs/*.md + mockups/*.png |
| `/api <名前>` | docs/api/*.yaml (OpenAPI) |
| `/schema <テーブル>` | migrations/*.sql |

### 実装フェーズ

| コマンド | 担当 |
|---------|------|
| `/implement` | Claude（設計書から実装） |
| `/test` | Codex（受入条件からテスト） |
| `/review` | Codex（コードレビュー） |
| `/deploy` | Claude（デプロイ） |

### 分析・調査

| コマンド | 担当 |
|---------|------|
| `/analyze` | Gemini（大規模コード解析） |
| `/research <質問>` | Gemini（技術リサーチ） |
| `/refactor <path>` | Gemini（リファクタ提案） |

---

## 成果物構造

```
docs/
├── requirements/     # 要件定義（ユーザーストーリー、受入条件）
├── specs/            # 画面設計（コンポーネント、状態遷移）
├── api/              # API設計（OpenAPI 3.0）
├── decisions/        # 設計判断の記録
└── reviews/          # レビュー記録
mockups/              # 画面モックアップ（PNG）
migrations/           # DBマイグレーション（SQL）
```

---

## 使用例

```bash
# 完全ワークフロー
/project ユーザー認証

# 個別実行
/requirements ユーザー認証
/spec ログイン画面
/api 認証API
/schema users
/implement
/test
/review
/deploy
```

---

## 動作環境

- macOS / Linux / WSL2
- Node.js 18+
- Claude Code / Codex / Gemini CLI

---

MIT License | [Issue](https://github.com/yu010101/claude-codex-collab/issues)
