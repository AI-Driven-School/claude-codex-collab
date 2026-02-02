# Claude Code のトークン消費を 95% 削減

コードレビュー・テスト作成・ドキュメント生成を Codex に自動委譲。
Claude Code は設計と実装に集中。API課金を大幅カット。

| タスク | Before | After | 削減 |
|-------|--------|-------|------|
| コードレビュー | 53,000 | 2,500 | **-95%** |
| テスト作成 | 30,000 | 3,000 | **-90%** |
| ドキュメント | 20,000 | 2,000 | **-90%** |

---

## インストール（10秒）

```bash
curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install-fullstack.sh | bash -s -- my-app
```

インストール後、`claude` を起動するだけ。

---

## 使い方

### 機能追加

```bash
/feature ユーザー認証
```

```
[設計] → [UI生成] → [実装] → [テスト] → [レビュー] → [デプロイ]
Claude   Claude    Claude   Codex    Codex     Vercel
```

自動で設計からデプロイまで。テスト・レビューは Codex が担当。

### バグ修正

```bash
/fix ログインエラー
```

原因調査 → 修正 → レビュー → デプロイ を自動実行。

### UI生成

```bash
/ui ログインフォーム
/page ダッシュボード
```

AI臭くない、プロダクション品質のUIを生成。

### デプロイ

```bash
/deploy          # 本番デプロイ
/deploy preview  # プレビュー
```

---

## なぜ速いのか

```
┌─────────────────────────────────────────────────────────┐
│  あなたの指示                                            │
│       ↓                                                 │
│  ┌─────────────┐    ┌─────────────┐                    │
│  │ Claude Code │───→│   Codex     │                    │
│  │  設計・実装  │    │ テスト・レビュー│                    │
│  └─────────────┘    └─────────────┘                    │
│       ↓                   ↓                            │
│  ┌─────────────────────────────────┐                   │
│  │         完成・デプロイ            │                   │
│  └─────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

Claude Code が得意な**設計・複雑な実装**に集中。
定型作業（テスト・レビュー・ドキュメント）は Codex に自動委譲。

---

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `/feature <名前>` | 新機能追加（設計→実装→テスト→デプロイ） |
| `/fix <内容>` | バグ修正（調査→修正→レビュー→デプロイ） |
| `/ui <名前>` | UIコンポーネント生成 |
| `/page <名前>` | ページ全体のUI生成 |
| `/deploy` | 本番デプロイ |
| `/review` | コードレビュー実行 |
| `/test <path>` | テスト生成 |

---

## 含まれるもの

- **CLAUDE.md** - 自動委譲ルール設定
- **カスタムスキル** - 上記コマンドの定義
- **委譲スクリプト** - Codex連携の自動化
- **モックアップ生成** - HTML/SwiftUI → PNG

---

## 最小構成版

Supabase/Vercel なしで、Claude Code + Codex の連携のみ使いたい場合：

```bash
curl -fsSL https://raw.githubusercontent.com/yu010101/claude-codex-collab/main/install.sh | bash
```

---

## ライセンス

MIT License

---

## 貢献

[Issue](https://github.com/yu010101/claude-codex-collab/issues) / [Pull Request](https://github.com/yu010101/claude-codex-collab/pulls) 歓迎
