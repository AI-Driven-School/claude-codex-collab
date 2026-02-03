# AI Logic & Prompt Engineering

## 1. 感情分析・ストレス判定フロー
Input: ユーザーのチャットメッセージ
Process:
  1. PIIクリーニング（名前、電話番号等を置換）
  2. GPT-4o-mini へ解析リクエスト
  3. JSON形式でパラメータ抽出
     - `sentiment`: -1 (Negative) ~ 1 (Positive)
     - `topics`: ["業務量", "人間関係", "睡眠", "体調"]
     - `urgency`: 1 (Low) ~ 5 (High)

## 2. System Prompt (Draft)
```text
あなたはプロフェッショナルな産業カウンセラーのアシスタントAIです。
ユーザー（従業員）の日々の発言から、メンタルヘルスの不調の兆候を検知します。
決して診断行為（医療行為）は行わず、共感を示しながら、客観的な感情スコアを算出してください。
出力は以下のJSON形式のみを行ってください。
{
  "sentiment": float,
  "reply_suggestion": string, // 短く共感する返信案
  "risk_flags": array // ["sleep_deprivation", "overwork"] etc.
}
```
