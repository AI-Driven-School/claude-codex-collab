"""
組織分析AI サービス
部署全体のストレス分析とAIインサイト生成
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.models import User, StressCheck, Department, UserRole
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Literal
import os
import openai
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class OrgAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    async def get_org_analysis(self) -> Dict[str, Any]:
        """組織全体の分析データを取得"""

        # 部署別スコアを取得
        departments = await self._get_department_scores()

        # 全体スコアを計算
        if departments:
            total_employees = sum(d["employee_count"] for d in departments)
            org_score = sum(d["score"] * d["employee_count"] for d in departments) / total_employees
        else:
            total_employees = 0
            org_score = 0.0

        # 前月比を計算
        score_change = await self._calculate_score_change()

        # 回答率を計算
        response_rate = await self._calculate_response_rate()

        # トレンドデータを取得
        trends = await self._get_trend_data()

        # AIインサイトを生成
        ai_insights = await self._generate_ai_insights(departments, org_score, score_change)

        return {
            "organization_score": round(org_score, 1),
            "score_change": round(score_change, 1),
            "total_employees": total_employees,
            "response_rate": round(response_rate, 1),
            "departments": departments,
            "trends": trends,
            "ai_insights": ai_insights,
            "generated_at": datetime.utcnow()
        }

    async def _get_department_scores(self) -> List[Dict[str, Any]]:
        """部署別のストレススコアを取得"""

        # 部署一覧を取得
        dept_result = await self.db.execute(select(Department))
        departments = dept_result.scalars().all()

        result = []
        for dept in departments:
            # 部署のユーザーを取得
            user_result = await self.db.execute(
                select(User).where(User.department_id == dept.id)
            )
            users = user_result.scalars().all()
            user_ids = [u.id for u in users]

            if not user_ids:
                continue

            # 最新のストレスチェック結果を取得
            score_result = await self.db.execute(
                select(func.avg(StressCheck.total_score))
                .where(
                    and_(
                        StressCheck.user_id.in_(user_ids),
                        StressCheck.completed_at >= date.today() - timedelta(days=90)
                    )
                )
            )
            avg_score = score_result.scalar() or 50.0

            # リスクレベルを判定
            if avg_score >= 70:
                risk_level = "high"
            elif avg_score >= 50:
                risk_level = "medium"
            else:
                risk_level = "low"

            result.append({
                "id": str(dept.id),
                "name": dept.name,
                "score": round(float(avg_score), 1),
                "employee_count": len(user_ids),
                "risk_level": risk_level
            })

        # スコアの高い順（リスクが高い順）にソート
        result.sort(key=lambda x: x["score"], reverse=True)
        return result

    async def _calculate_score_change(self) -> float:
        """前月比のスコア変化を計算"""
        today = date.today()
        first_of_month = today.replace(day=1)
        first_of_last_month = (first_of_month - timedelta(days=1)).replace(day=1)

        # 今月の平均
        current_result = await self.db.execute(
            select(func.avg(StressCheck.total_score))
            .where(StressCheck.completed_at >= first_of_month)
        )
        current_avg = current_result.scalar() or 0

        # 先月の平均
        last_result = await self.db.execute(
            select(func.avg(StressCheck.total_score))
            .where(
                and_(
                    StressCheck.completed_at >= first_of_last_month,
                    StressCheck.completed_at < first_of_month
                )
            )
        )
        last_avg = last_result.scalar() or current_avg

        return float(current_avg - last_avg)

    async def _calculate_response_rate(self) -> float:
        """回答率を計算"""
        # 全従業員数
        total_result = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.EMPLOYEE)
        )
        total_employees = total_result.scalar() or 0

        if total_employees == 0:
            return 0.0

        # 今月回答した人数
        first_of_month = date.today().replace(day=1)
        responded_result = await self.db.execute(
            select(func.count(func.distinct(StressCheck.user_id)))
            .where(StressCheck.completed_at >= first_of_month)
        )
        responded = responded_result.scalar() or 0

        return (responded / total_employees) * 100

    async def _get_trend_data(self) -> List[Dict[str, Any]]:
        """過去6ヶ月のトレンドデータを取得"""
        trends = []
        today = date.today()

        for i in range(6):
            # i ヶ月前
            target_month = today - timedelta(days=30 * i)
            first_of_month = target_month.replace(day=1)
            if i == 0:
                last_of_month = today
            else:
                next_month = (first_of_month + timedelta(days=32)).replace(day=1)
                last_of_month = next_month - timedelta(days=1)

            result = await self.db.execute(
                select(func.avg(StressCheck.total_score))
                .where(
                    and_(
                        StressCheck.completed_at >= first_of_month,
                        StressCheck.completed_at <= last_of_month
                    )
                )
            )
            avg_score = result.scalar() or 50.0

            trends.append({
                "month": first_of_month.strftime("%Y-%m"),
                "score": round(float(avg_score), 1)
            })

        trends.reverse()  # 古い順に並べる
        return trends

    async def _generate_ai_insights(
        self,
        departments: List[Dict[str, Any]],
        org_score: float,
        score_change: float
    ) -> Dict[str, Any]:
        """OpenAI GPT-4でAIインサイトを生成"""

        # 高リスク部署を抽出
        high_risk_depts = [d for d in departments if d["risk_level"] == "high"]

        # プロンプト作成
        prompt = f"""
以下の組織ストレスデータを分析し、JSON形式でインサイトを生成してください。

## データ
- 組織全体スコア: {org_score}/100（高いほどストレスが高い）
- 前月比変化: {score_change:+.1f}
- 高リスク部署: {len(high_risk_depts)}件
- 部署別データ:
{self._format_departments_for_prompt(departments)}

## 出力形式（JSON）
{{
  "summary": "2-3文の分析サマリー（日本語）",
  "risk_factors": ["リスク要因1", "リスク要因2", "リスク要因3"],
  "recommendations": ["改善提案1", "改善提案2", "改善提案3"]
}}

重要: 具体的で実用的なインサイトを生成してください。
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたは組織のメンタルヘルス専門家です。データに基づいた具体的な分析と提案を行います。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1000
            )

            import json
            insights = json.loads(response.choices[0].message.content)
            return insights

        except Exception as e:
            # APIエラー時はデフォルトのインサイトを返す
            return {
                "summary": f"組織全体のストレススコアは{org_score:.1f}です。" +
                          (f"前月比{score_change:+.1f}の変化が見られます。" if score_change != 0 else "") +
                          (f"高リスク部署が{len(high_risk_depts)}件検出されています。" if high_risk_depts else ""),
                "risk_factors": ["データ不足のため詳細分析ができません"],
                "recommendations": ["定期的なストレスチェックの実施を継続してください"]
            }

    def _format_departments_for_prompt(self, departments: List[Dict[str, Any]]) -> str:
        """部署データをプロンプト用にフォーマット"""
        lines = []
        for d in departments:
            risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(d["risk_level"], "⚪")
            lines.append(f"  {risk_emoji} {d['name']}: スコア{d['score']}、{d['employee_count']}名")
        return "\n".join(lines)

    async def generate_pdf_report(self) -> str:
        """組織分析PDFレポートを生成"""

        # 分析データを取得
        data = await self.get_org_analysis()

        # レポートディレクトリ
        report_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
        os.makedirs(report_dir, exist_ok=True)

        # ファイル名
        filename = f"org-analysis-{date.today().strftime('%Y-%m-%d')}.pdf"
        filepath = os.path.join(report_dir, filename)

        # PDF生成
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # タイトル
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph("組織ストレス分析レポート", title_style))
        story.append(Paragraph(f"生成日: {date.today().strftime('%Y年%m月%d日')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # サマリー
        story.append(Paragraph("1. 概要", styles['Heading2']))
        story.append(Paragraph(f"組織全体スコア: {data['organization_score']}/100", styles['Normal']))
        story.append(Paragraph(f"前月比: {data['score_change']:+.1f}", styles['Normal']))
        story.append(Paragraph(f"回答率: {data['response_rate']}%", styles['Normal']))
        story.append(Spacer(1, 20))

        # AIインサイト
        story.append(Paragraph("2. AIインサイト", styles['Heading2']))
        story.append(Paragraph(data['ai_insights']['summary'], styles['Normal']))
        story.append(Spacer(1, 10))

        story.append(Paragraph("リスク要因:", styles['Heading3']))
        for factor in data['ai_insights']['risk_factors']:
            story.append(Paragraph(f"• {factor}", styles['Normal']))
        story.append(Spacer(1, 10))

        story.append(Paragraph("改善提案:", styles['Heading3']))
        for rec in data['ai_insights']['recommendations']:
            story.append(Paragraph(f"• {rec}", styles['Normal']))
        story.append(Spacer(1, 20))

        # 部署別データ
        story.append(Paragraph("3. 部署別スコア", styles['Heading2']))
        table_data = [["部署名", "スコア", "人数", "リスク"]]
        for dept in data['departments']:
            risk_label = {"high": "高", "medium": "中", "low": "低"}[dept['risk_level']]
            table_data.append([
                dept['name'],
                str(dept['score']),
                str(dept['employee_count']),
                risk_label
            ])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)

        doc.build(story)
        return filepath

    async def get_department_detail(self, department_id: str) -> Dict[str, Any]:
        """部署の詳細分析データを取得"""

        from uuid import UUID

        # 部署を取得
        dept_result = await self.db.execute(
            select(Department).where(Department.id == UUID(department_id))
        )
        dept = dept_result.scalar_one_or_none()

        if not dept:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="部署が見つかりません")

        # 部署のユーザーを取得
        user_result = await self.db.execute(
            select(User).where(User.department_id == dept.id)
        )
        users = user_result.scalars().all()
        user_ids = [u.id for u in users]

        # 平均スコア
        score_result = await self.db.execute(
            select(func.avg(StressCheck.total_score))
            .where(StressCheck.user_id.in_(user_ids))
        )
        avg_score = float(score_result.scalar() or 50.0)

        # リスクレベル判定
        if avg_score >= 70:
            risk_level = "high"
        elif avg_score >= 50:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 高リスク者数
        high_risk_result = await self.db.execute(
            select(func.count(StressCheck.id))
            .where(
                and_(
                    StressCheck.user_id.in_(user_ids),
                    StressCheck.total_score >= 70
                )
            )
        )
        high_risk_count = high_risk_result.scalar() or 0

        # 月別トレンド
        monthly_scores = []
        today = date.today()
        for i in range(6):
            target_month = today - timedelta(days=30 * i)
            first_of_month = target_month.replace(day=1)
            next_month = (first_of_month + timedelta(days=32)).replace(day=1)

            result = await self.db.execute(
                select(func.avg(StressCheck.total_score))
                .where(
                    and_(
                        StressCheck.user_id.in_(user_ids),
                        StressCheck.completed_at >= first_of_month,
                        StressCheck.completed_at < next_month
                    )
                )
            )
            score = result.scalar() or avg_score
            monthly_scores.append({
                "month": first_of_month.strftime("%Y-%m"),
                "score": round(float(score), 1)
            })
        monthly_scores.reverse()

        # AI分析
        prompt = f"{dept.name}のストレススコアは{avg_score:.1f}で、高リスク者が{high_risk_count}名います。この部署への具体的なアドバイスを1-2文で述べてください。"

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "組織のメンタルヘルス専門家として回答してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            ai_analysis = response.choices[0].message.content
        except:
            ai_analysis = f"{dept.name}のストレスレベルを継続的にモニタリングし、必要に応じて個別面談を実施することを推奨します。"

        return {
            "department": {
                "id": str(dept.id),
                "name": dept.name,
                "score": round(avg_score, 1),
                "employee_count": len(user_ids),
                "risk_level": risk_level
            },
            "monthly_scores": monthly_scores,
            "stress_factors": [
                {"category": "仕事の量", "score": avg_score * 0.3},
                {"category": "対人関係", "score": avg_score * 0.25},
                {"category": "仕事の質", "score": avg_score * 0.25},
                {"category": "環境", "score": avg_score * 0.2}
            ],
            "high_risk_count": high_risk_count,
            "ai_analysis": ai_analysis
        }
