# 要件定義: 組織分析AI

**作成日**: 2026-02-02
**ステータス**: Approved
**作成者**: Claude Code

---

## ユーザーストーリー

AS A 人事担当者・経営層
I WANT TO 組織全体のストレス傾向をAIが分析したレポートを見たい
SO THAT データに基づいた意思決定と早期介入ができる

---

## 受入条件

### 機能要件

- [x] 部署別ストレススコアの集計・可視化
- [x] AIによる傾向分析コメント生成
- [x] 前月比・前年比の変化表示
- [x] リスク部署の自動検出とアラート
- [x] 改善提案の自動生成
- [x] PDFレポート出力機能

### 非機能要件

- **パフォーマンス**: 分析処理10秒以内
- **セキュリティ**: 管理者権限必須、個人情報匿名化
- **アクセシビリティ**: WCAG 2.1 AA準拠

---

## 画面仕様

### 1. 組織分析ダッシュボード (`/admin/org-analysis`)

| 要素 | 説明 |
|------|------|
| 組織全体スコア | 全従業員の平均ストレススコア |
| 部署別ヒートマップ | 部署ごとのストレスレベルを色で表示 |
| トレンドグラフ | 過去6ヶ月のスコア推移 |
| AIインサイト | GPTによる分析コメント |
| リスクアラート | 高ストレス部署の警告 |
| 改善提案 | AIが提案するアクションアイテム |
| レポート出力ボタン | PDF形式でダウンロード |

---

## API仕様

### GET /api/v1/admin/org-analysis

組織全体の分析データを取得

**Response:**
```json
{
  "organization_score": 65.5,
  "score_change": -2.3,
  "total_employees": 150,
  "response_rate": 85.5,
  "departments": [
    {
      "id": "dept-1",
      "name": "営業部",
      "score": 72.5,
      "employee_count": 30,
      "risk_level": "high"
    }
  ],
  "trends": [
    {"month": "2026-01", "score": 67.8},
    {"month": "2025-12", "score": 65.5}
  ],
  "ai_insights": {
    "summary": "全体的なストレスレベルは...",
    "risk_factors": ["残業時間増加", "人員不足"],
    "recommendations": ["1on1ミーティングの強化", "業務分担の見直し"]
  }
}
```

### POST /api/v1/admin/org-analysis/generate-report

PDFレポートを生成

**Response:**
```json
{
  "report_url": "/reports/org-analysis-2026-02.pdf",
  "generated_at": "2026-02-02T15:00:00Z"
}
```

---

## データモデル

```python
class OrgAnalysisResult:
    organization_score: float
    score_change: float
    departments: List[DepartmentScore]
    trends: List[TrendData]
    ai_insights: AIInsights
    generated_at: datetime

class DepartmentScore:
    id: str
    name: str
    score: float
    employee_count: int
    risk_level: Literal["low", "medium", "high"]

class AIInsights:
    summary: str
    risk_factors: List[str]
    recommendations: List[str]
```

---

## 制約事項

- バックエンド: FastAPI (Python)
- フロントエンド: Next.js 14 App Router, TypeScript
- AI: OpenAI GPT-4
- 既存の認証・権限システムを使用
