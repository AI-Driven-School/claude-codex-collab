# Twitter/X 投稿原稿

## メインツイート（1/7）

```
Claude Code 単体だと遅いので、Codex と分業させる OSS を作った

結果:
・コスト 75%削減
・一人開発でも設計書が残る
・AI同士でレビューさせるから安心

/project コマンド1つで、設計→実装→テスト→レビューまで自動化

https://github.com/AI-Driven-School/claude-codex-collab
```

**添付**: promo.gif

---

## スレッド（2/7）

```
課題:

Claude Code は賢いけど、
「CRUDのAPI作って」みたいな単純作業でも課金される

設計判断は Claude が強い
でも実装は Codex (ChatGPT Pro含む) の方が速い

なら分業させればいい
```

---

## スレッド（3/7）

```
解決策:

Claude → 設計・判断・レビュー（ここだけ課金）
Codex → 実装・テスト（$0、ChatGPT Proに含む）
Gemini → 大規模解析（無料）

Before: 1機能 $1.00
After:  1機能 $0.25（75%削減）
```

---

## スレッド（4/7）

```
ワークフロー:

/project ユーザー認証

[1/6] 要件定義 → Claude
[2/6] API設計 → Claude
[3/6] 実装 → Codex ★ $0
[4/6] テスト → Codex ★ $0
[5/6] レビュー → Claude
[6/6] デプロイ → 承認後

各フェーズで承認/却下できる
AIに全部任せるのが怖くても大丈夫
```

---

## スレッド（5/7）

```
「AIにレビューさせる」が意外と安心

Codex は速いけど雑な時がある
→ Claude がレビューして設計書との整合性をチェック

人間は最終確認だけ

AI同士で牽制させると、
1つのAIに全部任せるより信頼できる
```

---

## スレッド（6/7）

```
実際に作ったもの:

メンタルヘルスSaaSに「組織分析AI」機能を追加

/project 組織分析AI

→ 要件定義
→ API設計（OpenAPI）
→ 画面設計
→ バックエンド実装
→ フロントエンド実装
→ E2Eテスト 10ケース
→ レビュー文書

これが全部自動で生成される
```

---

## スレッド（7/7）

```
Phase 1 完全無料で公開中

必要なもの:
・Claude Code
・ChatGPT Pro（$200/月、Codex用）
・Gemini CLI（無料）

ChatGPT Pro に入ってる人は今すぐ使える

https://github.com/AI-Driven-School/claude-codex-collab

⭐ Star お願いします

#ClaudeCode #生成AI #個人開発 #OSS
```

---

## 単発ツイート案（記事公開時）

```
記事書きました

「Claude Code 単体だと遅いので、Codex と分業させる OSS を作ってみた」

・課題: Claude は賢いが、単純作業も課金される
・解決: 設計は Claude、実装は Codex
・結果: 75%コスト削減 + 設計書が残る

[Zenn記事URL]

#ClaudeCode #Codex #AI開発
```

---

## 投稿タイミング

- **平日**: 12:00-13:00（昼休み）or 21:00-22:00（帰宅後）
- **土日**: 10:00-11:00

---

## ハッシュタグ

```
#ClaudeCode #ChatGPT #Codex #生成AI #AI開発 #個人開発 #OSS
```
