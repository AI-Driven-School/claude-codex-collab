"""PDF生成サービス"""
from io import BytesIO
from datetime import datetime, date
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
FONT_MINCHO = 'HeiseiMin-W3'
FONT_GOTHIC = 'HeiseiKakuGo-W5'

def get_japanese_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='JapaneseTitle', fontName=FONT_GOTHIC, fontSize=18, leading=24, alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name='JapaneseHeading', fontName=FONT_GOTHIC, fontSize=14, leading=18, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name='JapaneseBody', fontName=FONT_MINCHO, fontSize=10, leading=16, spaceAfter=6))
    return styles

def create_header(title, subtitle=None):
    styles = get_japanese_styles()
    elements = [Paragraph(title, styles['JapaneseTitle'])]
    if subtitle: elements.append(Paragraph(subtitle, styles['JapaneseBody']))
    elements.append(Spacer(1, 10*mm))
    return elements

def stress_level(score, max_score=4.0):
    r = score / max_score
    if r >= 0.75: return "高"
    elif r >= 0.5: return "やや高"
    elif r >= 0.25: return "普通"
    return "低"

class StressCheckPDFGenerator:
    def generate_individual_report(self, user_name, period, total_score, is_high_stress, job_stress_score, stress_reaction_score, support_score, satisfaction_score, answers=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = get_japanese_styles()
        elements = create_header("ストレスチェック結果報告書", f"実施期間: {period.strftime('%Y年%m月')}")
        elements.append(Paragraph("1. 基本情報", styles['JapaneseHeading']))
        info = Table([["氏名", user_name], ["実施日", datetime.now().strftime("%Y年%m月%d日")], ["総合スコア", str(total_score)], ["判定結果", "高ストレス者" if is_high_stress else "通常範囲"]], colWidths=[50*mm, 100*mm])
        info.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_GOTHIC), ('FONTSIZE', (0,0), (-1,-1), 10), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 8)]))
        elements.extend([info, Spacer(1, 10*mm), Paragraph("2. 詳細スコア", styles['JapaneseHeading'])])
        scores = Table([["項目", "スコア", "レベル"], ["仕事のストレス要因", f"{job_stress_score:.2f}", stress_level(job_stress_score)], ["心身のストレス反応", f"{stress_reaction_score:.2f}", stress_level(stress_reaction_score)], ["周囲のサポート", f"{support_score:.2f}", stress_level(4.0-support_score)], ["満足度", f"{satisfaction_score:.2f}", stress_level(4.0-satisfaction_score)]], colWidths=[60*mm, 40*mm, 50*mm])
        scores.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_GOTHIC), ('FONTSIZE', (0,0), (-1,-1), 9), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2b6cb0')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 6)]))
        elements.extend([scores, Spacer(1, 10*mm), Paragraph("3. 判定結果と助言", styles['JapaneseHeading'])])
        elements.append(Paragraph("高ストレスと判定されました。産業医との面談を検討してください。" if is_high_stress else "通常範囲です。引き続き健康管理に努めてください。", styles['JapaneseBody']))
        elements.extend([Spacer(1, 15*mm), Paragraph(f"作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} | StressAgent Pro", styles['JapaneseBody'])])
        doc.build(elements)
        buffer.seek(0)
        return buffer

class GroupAnalysisPDFGenerator:
    def generate_company_report(self, company_name, period, total_employees, high_stress_count, completion_rate, average_stress_score, department_stats, recommendations):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = get_japanese_styles()
        elements = create_header("ストレスチェック集団分析報告書", f"{company_name} | 対象期間: {period.strftime('%Y年%m月')}")
        elements.append(Paragraph("1. 全体サマリー", styles['JapaneseHeading']))
        rate = (high_stress_count / total_employees * 100) if total_employees > 0 else 0
        summary = Table([["項目", "数値", "備考"], ["対象従業員数", f"{total_employees}名", ""], ["受検率", f"{completion_rate:.1f}%", "目標: 80%以上"], ["高ストレス者数", f"{high_stress_count}名", f"全体の{rate:.1f}%"], ["平均スコア", f"{average_stress_score:.1f}", ""]], colWidths=[50*mm, 40*mm, 60*mm])
        summary.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_GOTHIC), ('FONTSIZE', (0,0), (-1,-1), 10), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2b6cb0')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 8)]))
        elements.extend([summary, Spacer(1, 10*mm), Paragraph("2. リスク評価", styles['JapaneseHeading'])])
        if rate >= 20: msg = "高リスク - 早急な対策が必要です"
        elif rate >= 10: msg = "中リスク - 対策を検討してください"
        else: msg = "低リスク - 引き続きモニタリングを継続してください"
        elements.extend([Paragraph(f"リスクレベル: {msg}", styles['JapaneseBody']), Spacer(1, 10*mm)])
        if department_stats:
            elements.append(Paragraph("3. 部署別統計", styles['JapaneseHeading']))
            data = [["部署名", "従業員数", "高ストレス者数", "平均スコア"]] + [[d.get("department_name","-"), f"{d.get('employee_count',0)}名", f"{d.get('high_stress_count',0)}名", f"{d.get('average_score',0):.1f}"] for d in department_stats]
            t = Table(data, colWidths=[50*mm, 35*mm, 35*mm, 30*mm])
            t.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_GOTHIC), ('FONTSIZE', (0,0), (-1,-1), 9), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a5568')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 6)]))
            elements.extend([t, Spacer(1, 10*mm)])
        elements.append(Paragraph("4. AI改善提案", styles['JapaneseHeading']))
        if recommendations:
            for r in recommendations: elements.append(Paragraph(f"- {r.get('title','')}", styles['JapaneseBody']))
        else: elements.append(Paragraph("特別な改善提案はありません。", styles['JapaneseBody']))
        elements.extend([Spacer(1, 15*mm), Paragraph(f"作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} | StressAgent Pro", styles['JapaneseBody'])])
        doc.build(elements)
        buffer.seek(0)
        return buffer

class DepartmentReportPDFGenerator:
    def generate_department_report(self, company_name, department_name, period, employee_count, high_stress_count, average_score, job_stress_avg, stress_reaction_avg, support_avg, satisfaction_avg, trend_data=None, comparison_data=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = get_japanese_styles()
        elements = create_header("部署別ストレスチェック分析報告書", f"{company_name} - {department_name} | {period.strftime('%Y年%m月')}")
        elements.append(Paragraph("1. 部署サマリー", styles['JapaneseHeading']))
        rate = (high_stress_count / employee_count * 100) if employee_count > 0 else 0
        summary = Table([["項目", "数値"], ["部署名", department_name], ["所属人数", f"{employee_count}名"], ["高ストレス者数", f"{high_stress_count}名 ({rate:.1f}%)"], ["平均スコア", f"{average_score:.1f}"]], colWidths=[60*mm, 90*mm])
        summary.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_GOTHIC), ('FONTSIZE', (0,0), (-1,-1), 10), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2b6cb0')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 8)]))
        elements.extend([summary, Spacer(1, 10*mm), Paragraph("2. 詳細スコア分析", styles['JapaneseHeading'])])
        scores = Table([["項目", "部署平均", "レベル"], ["仕事のストレス要因", f"{job_stress_avg:.2f}", stress_level(job_stress_avg)], ["心身のストレス反応", f"{stress_reaction_avg:.2f}", stress_level(stress_reaction_avg)], ["周囲のサポート", f"{support_avg:.2f}", stress_level(4.0-support_avg)], ["満足度", f"{satisfaction_avg:.2f}", stress_level(4.0-satisfaction_avg)]], colWidths=[60*mm, 40*mm, 50*mm])
        scores.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_GOTHIC), ('FONTSIZE', (0,0), (-1,-1), 10), ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a5568')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 8)]))
        elements.extend([scores, Spacer(1, 10*mm), Paragraph("3. 課題と改善提案", styles['JapaneseHeading'])])
        issues = []
        if job_stress_avg >= 3.0: issues.append("仕事のストレス要因が高い傾向にあります。")
        if stress_reaction_avg >= 3.0: issues.append("心身のストレス反応が高い傾向にあります。")
        if support_avg < 2.0: issues.append("周囲のサポートが不足している傾向にあります。")
        if issues:
            for i in issues: elements.append(Paragraph(f"- {i}", styles['JapaneseBody']))
        else: elements.append(Paragraph("特に顕著な課題は見られません。", styles['JapaneseBody']))
        elements.extend([Spacer(1, 15*mm), Paragraph(f"作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} | StressAgent Pro", styles['JapaneseBody'])])
        doc.build(elements)
        buffer.seek(0)
        return buffer

def get_stress_check_pdf_generator(): return StressCheckPDFGenerator()
def get_group_analysis_pdf_generator(): return GroupAnalysisPDFGenerator()
def get_department_report_pdf_generator(): return DepartmentReportPDFGenerator()
