# 3つのAIを、適材適所で

[![GitHub Sponsors](https://img.shields.io/github/sponsors/yu010101?style=for-the-badge&logo=github&label=Sponsor)](https://github.com/sponsors/yu010101)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Claude   ──設計──▶   Codex   ──実装──▶   Claude          │
│   (推論)              (爆速)              (レビュー)        │
│                          │                                  │
│                       Gemini                                │
│                      (大規模解析)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Claude** で設計、**Codex** で爆速実装、**Gemini** で大規模解析。
各AIの強みを活かした分業で、品質とスピードを両立。

---

## ベンチマーク（実測値）

### 結果サマリー

```
┌─────────────────────────────────────────────────────────────┐
│                    実測ベンチマーク結果                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【単純タスク】新規ファイル作成                             │
│                                                             │
│     カウンター   Codex ████████████ 21.8秒  $0   ← 勝者    │
│                  Claude ██████████████ 24.8秒  $0.02       │
│                                                             │
│     認証API      Codex ████████████████ 46.7秒  $0  ← 勝者 │
│                  Claude ██████████████████ 55.7秒  $0.12   │
│                                                             │
│  【複雑タスク】既存15K行へのDiscord連携追加                 │
│                                                             │
│     時間         Claude ████████████ 3分0秒     ← 勝者     │
│                  Codex ██████████████████ 5分3秒            │
│                                                             │
│     品質         Claude 34KB（包括的）  ← 勝者              │
│                  Codex 16KB（基本のみ）                     │
│                                                             │
│  【大規模解析】15K行プロジェクト全体レポート                │
│                                                             │
│     速度         Claude ██████████ 3分6秒    ← 最速        │
│                  Codex ████████████████ 5分31秒             │
│                  Gemini ██████████████████ 6分58秒          │
│                                                             │
│     コスト       Gemini $0（無料）  ← 最安                  │
│                  Codex $0（ChatGPT Pro含む）                │
│                  Claude $0.75                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 使い分け早見表

| タスク種別 | 推奨AI | 理由 | コスト |
|-----------|--------|------|--------|
| 新規ファイル作成（単純） | **Codex** | 10-20%速い | $0 |
| 既存コード修正（複雑） | **Claude** | 40%速い、品質2倍 | 従量課金 |
| 大規模解析（〜10万行） | **Claude** | 最速、最詳細 | 従量課金 |
| 超大規模解析（10万行〜） | **Gemini** | 1Mトークン対応 | **無料** |

> 📊 [詳細なベンチマーク結果](./benchmarks/BENCHMARK_RESULTS.md)

---

## なぜ3AI連携？

```
単一AIの限界:
├─ Claude だけ → 単純タスクも課金、コスト高い
├─ Codex だけ → 複雑タスクで品質低下
└─ Gemini だけ → 実装精度が不安定

3AI連携の強み:
├─ 単純タスク → Codex（$0）
├─ 複雑タスク → Claude（高品質）
└─ 大規模解析 → Gemini（無料）
    ↓
  適材適所でコスト最小化 × 品質最大化
```

### コスト比較（3タスク実行時）

| 方式 | コスト |
|------|--------|
| Claude単体 | ~$1.00 |
| **3AI連携** | **~$0.25**（75%削減） |

※ ChatGPT Pro加入者の場合。Codex/Geminiは追加コストなし。

---

## クイックスタート

```bash
# インストール
curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install-fullstack.sh | bash -s -- my-app

# 開発開始
cd my-app
claude

# 機能を作る
> /project ユーザー認証
```

### 前提条件

| ツール | 必要なアカウント | コスト |
|--------|----------------|--------|
| Claude Code | Anthropic アカウント | 従量課金 |
| Codex | ChatGPT Plus/Pro | 月額に含む |
| Gemini | Google アカウント | 無料 |

---

## ワークフロー

```
> /project ユーザー認証

[1/6] Claude  要件定義を生成...
              → docs/requirements/auth.md
              承認？ [Y/n] Y ✓

[2/6] Claude  API設計を生成...
              → docs/api/auth.yaml
              承認？ [Y/n] Y ✓

[3/6] Codex   実装中...（full-auto）★メイン
              → src/app/login/page.tsx
              → src/lib/api/auth.ts

[4/6] Codex   テスト生成中...
              → tests/auth.spec.ts

[5/6] Claude  レビュー中...
              → 2件の改善提案

[6/6] Claude  デプロイ準備完了
              本番に出しますか？ [Y/n] Y

✅ https://my-app.vercel.app
```

### 各フェーズの担当AI

```
┌─────────────────────────────────────────────────────────────┐
│  フェーズ        AI        理由                             │
├─────────────────────────────────────────────────────────────┤
│  [1] 要件定義    Claude    推論・判断が必要                 │
│  [2] 設計        Claude    アーキテクチャ決定               │
│  [3] 実装        Codex     full-auto で爆速 ★コスト$0      │
│  [4] テスト      Codex     実装と一貫性 ★コスト$0          │
│  [5] レビュー    Claude    品質チェック                     │
│  [6] デプロイ    Claude    最終判断                         │
└─────────────────────────────────────────────────────────────┘
```

---

## コマンド一覧

### プロジェクト管理

| コマンド | 説明 |
|---------|------|
| `/project <機能>` | 設計→実装→デプロイの完全フロー |
| `/status` | 進捗確認 |

### 設計（Claude）

| コマンド | 説明 |
|---------|------|
| `/requirements <機能>` | 要件定義 |
| `/spec <画面>` | 画面設計 |
| `/api <エンドポイント>` | API設計 |
| `/review` | コードレビュー |

### 実装（Codex）

| コマンド | 説明 |
|---------|------|
| `/implement` | 設計書から実装（$0） |
| `/test` | テスト生成（$0） |

### 解析（Gemini）

| コマンド | 説明 |
|---------|------|
| `/analyze` | 大規模コード解析（無料） |
| `/research <質問>` | 技術リサーチ（無料） |

---

## 成果物

```
my-app/
├── docs/
│   ├── requirements/   # 要件定義（Claude）
│   ├── specs/          # 画面設計（Claude）
│   ├── api/            # API設計（Claude）
│   └── reviews/        # レビュー記録（Claude）
├── src/                # 実装コード（Codex）
└── tests/              # テスト（Codex）
```

---

## 動作環境

- macOS / Linux / WSL2
- Node.js 18+
- ChatGPT Plus/Pro（Codex用）

---

## ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [導入ガイド](./docs/GETTING_STARTED.md) | インストール・セットアップ |
| [ハンズオン](./docs/HANDS_ON_TUTORIAL.md) | TODOアプリを作るチュートリアル |
| [コマンド一覧](./docs/COMMANDS.md) | 全コマンドのリファレンス |
| [ベンチマーク](./benchmarks/BENCHMARK_RESULTS.md) | 実測データ詳細 |

---

## ライセンス

MIT License

[GitHub](https://github.com/yu010101/claude-codex-collab) | [Issues](https://github.com/yu010101/claude-codex-collab/issues) | [Sponsor](https://github.com/sponsors/yu010101)
