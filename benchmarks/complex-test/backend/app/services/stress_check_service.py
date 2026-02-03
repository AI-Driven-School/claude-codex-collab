"""
ストレスチェック計算サービス
"""
from typing import Dict
from datetime import date
from app.db.models import StressCheck
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_


def calculate_stress_scores(answers: Dict[str, int]) -> Dict[str, float]:
    """
    ストレスチェックの各スコアを計算
    
    Args:
        answers: { "q1": 4, "q2": 2, ... } 形式の回答データ
    
    Returns:
        各尺度のスコア
    """
    # 仕事のストレス要因スコア
    job_quantity = (answers.get("q1", 0) + answers.get("q2", 0) + answers.get("q3", 0) + answers.get("q4", 0)) / 4
    job_quality = (answers.get("q5", 0) + answers.get("q6", 0) + answers.get("q7", 0) + answers.get("q8", 0)) / 4
    control = (answers.get("q9", 0) + answers.get("q10", 0) + answers.get("q11", 0)) / 3
    suitability = (answers.get("q12", 0) + answers.get("q13", 0) + answers.get("q14", 0)) / 3
    relationships = (answers.get("q15", 0) + answers.get("q16", 0) + answers.get("q17", 0)) / 3
    job_stress_score = (job_quantity + job_quality + control + suitability + relationships) / 5

    # 心身のストレス反応スコア
    vitality = sum(answers.get(f"q{i}", 0) for i in range(18, 23)) / 5
    irritation = sum(answers.get(f"q{i}", 0) for i in range(23, 28)) / 5
    fatigue = sum(answers.get(f"q{i}", 0) for i in range(28, 33)) / 5
    anxiety = sum(answers.get(f"q{i}", 0) for i in range(33, 38)) / 5
    depression = sum(answers.get(f"q{i}", 0) for i in range(38, 43)) / 5
    physical_complaints = sum(answers.get(f"q{i}", 0) for i in range(43, 47)) / 4
    stress_reaction_score = (vitality + irritation + fatigue + anxiety + depression + physical_complaints) / 6

    # 周囲のサポートスコア
    supervisor_support = sum(answers.get(f"q{i}", 0) for i in range(47, 50)) / 3
    colleague_support = sum(answers.get(f"q{i}", 0) for i in range(50, 53)) / 3
    family_support = sum(answers.get(f"q{i}", 0) for i in range(53, 56)) / 3
    support_score = (supervisor_support + colleague_support + family_support) / 3

    # 満足度スコア
    satisfaction_score = (answers.get("q56", 0) + answers.get("q57", 0)) / 2

    # 総合スコア（簡易計算）
    total_score = sum(answers.values())

    return {
        "job_stress_score": job_stress_score,
        "stress_reaction_score": stress_reaction_score,
        "support_score": support_score,
        "satisfaction_score": satisfaction_score,
        "total_score": total_score,
    }


def is_high_stress(
    stress_reaction_score: float,
    job_stress_score: float,
    support_score: float
) -> bool:
    """
    高ストレス者判定ロジック
    
    Args:
        stress_reaction_score: 心身のストレス反応スコア
        job_stress_score: 仕事のストレス要因スコア
        support_score: 周囲のサポートスコア
    
    Returns:
        高ストレス者の場合True
    """
    # 条件1: ストレス反応が高い
    if stress_reaction_score >= 3.0:
        return True

    # 条件2: ストレス反応が中程度 かつ 仕事のストレス要因が高い
    if 2.0 <= stress_reaction_score < 3.0 and job_stress_score >= 3.0:
        return True

    # 条件3: ストレス反応が中程度 かつ サポートが低い
    if 2.0 <= stress_reaction_score < 3.0 and support_score < 2.0:
        return True

    return False


async def check_duplicate_stress_check(
    db: AsyncSession,
    user_id: str,
    period: date
) -> bool:
    """
    同一期間での重複受検チェック
    
    Returns:
        重複がある場合True
    """
    from uuid import UUID
    result = await db.execute(
        select(StressCheck).where(
            and_(
                StressCheck.user_id == UUID(user_id),
                StressCheck.period == period
            )
        )
    )
    return result.scalar_one_or_none() is not None
