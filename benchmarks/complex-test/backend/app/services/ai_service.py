"""
AI分析サービス（OpenAI API連携）
"""
from typing import Dict, List, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.utils.pii_filter import clean_pii
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """あなたはプロフェッショナルな産業カウンセラーのアシスタントAIです。
ユーザー（従業員）の日々の発言から、メンタルヘルスの不調の兆候を検知します。
決して診断行為（医療行為）は行わず、共感を示しながら、客観的な感情スコアを算出してください。
出力は以下のJSON形式のみを行ってください。
{
  "sentiment": float,  // -1.0 (Negative) ~ 1.0 (Positive)
  "topics": array,  // ["業務量", "人間関係", "睡眠", "体調"] など
  "urgency": int,  // 1 (Low) ~ 5 (High)
  "reply_suggestion": string,  // 短く共感する返信案
  "risk_flags": array  // ["sleep_deprivation", "overwork"] など
}
"""


def contains_inappropriate_content(text: str) -> bool:
    """
    不適切なコンテンツを検出（簡易実装）
    
    Args:
        text: チェック対象のテキスト
    
    Returns:
        不適切なコンテンツが含まれている場合True
    """
    inappropriate_keywords = [
        '暴力', '殺', '死', '自殺', '暴力的',
        '差別', '侮辱', '誹謗'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in inappropriate_keywords)


async def analyze_sentiment(message: str, reaction_time: Optional[float] = None) -> Dict:
    """
    チャットメッセージから感情分析を実行
    
    Args:
        message: ユーザーのメッセージ
        reaction_time: 反応速度（秒、オプション）
    
    Returns:
        感情分析結果
    """
    # 不適切なコンテンツチェック
    if contains_inappropriate_content(message):
        return {
            "sentiment": -0.5,
            "topics": [],
            "urgency": 3,
            "reply_suggestion": "不適切な内容が検出されました。",
            "risk_flags": ["inappropriate_content"]
        }
    
    # PIIクリーニング
    cleaned_message = clean_pii(message)

    # OpenAI API呼び出し
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": cleaned_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # デフォルト値の設定
        sentiment = result.get("sentiment", 0.0)
        topics = result.get("topics", [])
        urgency = result.get("urgency", 1)
        reply_suggestion = result.get("reply_suggestion", "お疲れ様です。")
        risk_flags = result.get("risk_flags", [])

        return {
            "sentiment": float(sentiment),
            "topics": topics,
            "urgency": int(urgency),
            "reply_suggestion": reply_suggestion,
            "risk_flags": risk_flags,
        }
    except Exception as e:
        # エラー時はデフォルト値を返す
        return {
            "sentiment": 0.0,
            "topics": [],
            "urgency": 1,
            "reply_suggestion": "お疲れ様です。",
            "risk_flags": [],
        }


async def generate_chat_reply(user_message: str) -> str:
    """
    チャットへの返信を生成

    Args:
        user_message: ユーザーのメッセージ

    Returns:
        AIからの返信
    """
    analysis = await analyze_sentiment(user_message)
    return analysis.get("reply_suggestion", "お疲れ様です。")


# メンタルヘルス相談用のシステムプロンプト
COUNSELOR_SYSTEM_PROMPT = """あなたは、企業で働く従業員のメンタルヘルスをサポートする、温かく共感的なAIカウンセラーです。

あなたの役割:
- 従業員の悩みや不安に寄り添い、共感を示す
- 傾聴し、気持ちを受け止める
- 必要に応じて、セルフケアのヒントを提供する
- 深刻な状況では、専門家への相談を優しく勧める

重要なガイドライン:
1. 決して医療診断や治療のアドバイスは行わない
2. 共感と傾聴を第一に、押し付けがましくならない
3. 短く、温かみのある返答を心がける（3-5文程度）
4. ユーザーの言葉を大切にし、否定しない
5. 緊急性が高い場合（自殺願望など）は、専門窓口への連絡を促す

返答は日本語で行い、敬語を使いつつも親しみやすいトーンで話してください。"""


async def generate_counselor_response(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    メンタルヘルス相談に対するAI応答を生成

    Args:
        user_message: ユーザーのメッセージ
        conversation_history: 会話履歴（オプション）
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    Returns:
        AIカウンセラーからの応答
    """
    # PIIクリーニング
    cleaned_message = clean_pii(user_message)

    # 会話履歴を構築
    messages = [{"role": "system", "content": COUNSELOR_SYSTEM_PROMPT}]

    # 過去の会話履歴を追加（最大10件まで）
    if conversation_history:
        for entry in conversation_history[-10:]:
            messages.append({
                "role": entry.get("role", "user"),
                "content": entry.get("content", "")
            })

    # 現在のメッセージを追加
    messages.append({"role": "user", "content": cleaned_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=500,
        )

        reply = response.choices[0].message.content
        return reply if reply else "お話を聞いています。もう少し詳しく教えていただけますか？"

    except Exception as e:
        # エラー時はフォールバック応答を返す
        return "お話しいただきありがとうございます。そのお気持ち、よく分かります。もう少し詳しく聞かせていただけますか？"


# 改善アクション提案用のシステムプロンプト
RECOMMENDATION_SYSTEM_PROMPT = """あなたは企業のメンタルヘルス改善を支援する産業保健コンサルタントです。
部署ごとのストレスチェック結果データを分析し、具体的で実行可能な改善アクションを提案してください。

以下の観点から改善提案を行ってください：
- 労働時間・残業の適正化
- 職場のコミュニケーション改善
- 業務量・役割の明確化
- メンタルヘルス支援体制
- 休暇取得の促進
- 職場環境の改善

出力は以下のJSON形式で、recommendations配列に2-4件の提案を含めてください：
{
  "recommendations": [
    {
      "title": "提案タイトル（15文字以内）",
      "description": "具体的な改善アクション（80文字以内）",
      "department_name": "対象部署名（該当する場合。全社向けの場合はnull）",
      "priority": "high" | "medium" | "low"
    }
  ]
}
"""


async def generate_improvement_recommendations(
    department_stats: List[Dict],
    overall_stats: Dict
) -> List[Dict]:
    """
    部署別統計データからAI改善提案を生成

    Args:
        department_stats: 部署別統計データのリスト
            [{"department_name": str, "average_score": float,
              "high_stress_count": int, "employee_count": int}]
        overall_stats: 全体統計
            {"total_employees": int, "high_stress_count": int,
             "average_stress_score": float, "stress_check_completion_rate": float}

    Returns:
        改善提案のリスト
    """
    # データがない場合は空のリストを返す
    if not department_stats and overall_stats.get("total_employees", 0) == 0:
        return []

    # プロンプト用のデータ整形
    data_summary = f"""
【全社統計】
- 総従業員数: {overall_stats.get('total_employees', 0)}名
- 高ストレス者数: {overall_stats.get('high_stress_count', 0)}名
- 平均ストレススコア: {overall_stats.get('average_stress_score', 0):.1f}
- ストレスチェック受検率: {overall_stats.get('stress_check_completion_rate', 0):.1f}%

【部署別統計】
"""

    for dept in department_stats:
        high_stress_rate = (
            dept.get('high_stress_count', 0) / dept.get('employee_count', 1) * 100
            if dept.get('employee_count', 0) > 0 else 0
        )
        data_summary += f"""
- {dept.get('department_name', '不明')}部署:
  - 従業員数: {dept.get('employee_count', 0)}名
  - 平均スコア: {dept.get('average_score', 0):.1f}
  - 高ストレス者: {dept.get('high_stress_count', 0)}名 ({high_stress_rate:.1f}%)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"以下のストレスチェック結果を分析し、改善提案を行ってください。\n{data_summary}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        recommendations = result.get("recommendations", [])

        # 各提案にIDを付与
        for idx, rec in enumerate(recommendations):
            rec["id"] = f"ai-rec-{idx + 1}"
            # 必須フィールドのデフォルト値設定
            rec.setdefault("title", "改善提案")
            rec.setdefault("description", "")
            rec.setdefault("department_name", None)
            rec.setdefault("priority", "medium")

        return recommendations

    except Exception as e:
        # エラー時はフォールバック提案を返す
        return _generate_fallback_recommendations(department_stats, overall_stats)


def _generate_fallback_recommendations(
    department_stats: List[Dict],
    overall_stats: Dict
) -> List[Dict]:
    """
    AI API呼び出し失敗時のフォールバック提案を生成

    Args:
        department_stats: 部署別統計データ
        overall_stats: 全体統計

    Returns:
        フォールバック提案のリスト
    """
    fallback_recommendations = []

    # 高ストレス者が多い場合
    high_stress_count = overall_stats.get('high_stress_count', 0)
    total_employees = max(overall_stats.get('total_employees', 1), 1)

    if high_stress_count > 0:
        high_stress_rate = high_stress_count / total_employees * 100
        if high_stress_rate > 20:
            fallback_recommendations.append({
                "id": "fallback-1",
                "title": "高ストレス者への個別対応",
                "description": f"高ストレス者が{high_stress_count}名検出されています。産業医面談の機会を設けることを推奨します。",
                "department_name": None,
                "priority": "high"
            })

    # 受検率が低い場合
    completion_rate = overall_stats.get('stress_check_completion_rate', 0)
    if completion_rate < 80:
        fallback_recommendations.append({
            "id": "fallback-2",
            "title": "ストレスチェック受検促進",
            "description": f"受検率が{completion_rate:.1f}%です。未受検者へのリマインドを実施してください。",
            "department_name": None,
            "priority": "medium"
        })

    # 部署別の高ストレス者チェック
    for dept in department_stats:
        dept_high_stress = dept.get('high_stress_count', 0)
        dept_employee_count = dept.get('employee_count', 0)

        if dept_high_stress > 0 and dept_employee_count > 0:
            dept_rate = dept_high_stress / dept_employee_count * 100
            if dept_rate > 30:
                dept_name = dept.get('department_name', '該当部署')
                fallback_recommendations.append({
                    "id": f"fallback-dept-{dept_name}",
                    "title": f"{dept_name}の業務改善",
                    "description": f"高ストレス者率が{dept_rate:.0f}%と高い傾向です。業務量の見直しやノー残業デーの導入を検討してください。",
                    "department_name": dept_name,
                    "priority": "high"
                })
                break  # 1つだけ追加

    return fallback_recommendations[:4]  # 最大4件
