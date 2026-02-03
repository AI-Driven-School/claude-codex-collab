"""
ストレスチェック関連エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import date, timedelta
from typing import Optional
from app.db.database import get_db
from app.db.models import User, StressCheck, UserRole, DraftAnswer
from app.models.stress_check import (
    StressCheckAnswer,
    StressCheckResult,
    StressCheckHistoryItem,
    NonTakenUser,
    NonTakenUsersResponse,
    DraftAnswerRequest,
    DraftAnswerResponse,
    MigrateDraftRequest
)
from app.services.stress_check_service import (
    calculate_stress_scores,
    is_high_stress,
    check_duplicate_stress_check
)
from app.routers.auth import get_current_user
from uuid import UUID

router = APIRouter(prefix="/api/v1/stress-check", tags=["stress-check"])


# 57項目の質問データ
STRESS_CHECK_QUESTIONS = [
    {"id": "q1", "text": "あなたの仕事について教えてください。", "category": "仕事のストレス要因"},
    {"id": "q2", "text": "仕事の量は適切ですか？", "category": "仕事のストレス要因"},
    {"id": "q3", "text": "仕事の質についてどう感じますか？", "category": "仕事のストレス要因"},
    {"id": "q4", "text": "仕事のコントロール感はありますか？", "category": "仕事のストレス要因"},
    {"id": "q5", "text": "仕事の適性についてどう感じますか？", "category": "仕事のストレス要因"},
    {"id": "q6", "text": "職場の人間関係は良好ですか？", "category": "仕事のストレス要因"},
    {"id": "q7", "text": "職場の雰囲気は良いですか？", "category": "仕事のストレス要因"},
    {"id": "q8", "text": "仕事の負担は適切ですか？", "category": "仕事のストレス要因"},
    {"id": "q9", "text": "仕事の裁量権はありますか？", "category": "仕事のストレス要因"},
    {"id": "q10", "text": "仕事のやりがいは感じますか？", "category": "仕事のストレス要因"},
    {"id": "q11", "text": "仕事の評価は適切ですか？", "category": "仕事のストレス要因"},
    {"id": "q12", "text": "仕事のスキルは適切ですか？", "category": "仕事のストレス要因"},
    {"id": "q13", "text": "仕事のキャリア展望はありますか？", "category": "仕事のストレス要因"},
    {"id": "q14", "text": "仕事の環境は良いですか？", "category": "仕事のストレス要因"},
    {"id": "q15", "text": "職場のコミュニケーションは良好ですか？", "category": "仕事のストレス要因"},
    {"id": "q16", "text": "職場のサポートはありますか？", "category": "仕事のストレス要因"},
    {"id": "q17", "text": "職場の協力関係は良好ですか？", "category": "仕事のストレス要因"},
    {"id": "q18", "text": "最近、活気を感じますか？", "category": "心身のストレス反応"},
    {"id": "q19", "text": "最近、イライラすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q20", "text": "最近、疲れを感じますか？", "category": "心身のストレス反応"},
    {"id": "q21", "text": "最近、不安を感じますか？", "category": "心身のストレス反応"},
    {"id": "q22", "text": "最近、気分が落ち込むことがありますか？", "category": "心身のストレス反応"},
    {"id": "q23", "text": "最近、体調不良を感じますか？", "category": "心身のストレス反応"},
    {"id": "q24", "text": "最近、睡眠の質は良いですか？", "category": "心身のストレス反応"},
    {"id": "q25", "text": "最近、食欲はありますか？", "category": "心身のストレス反応"},
    {"id": "q26", "text": "最近、集中力はありますか？", "category": "心身のストレス反応"},
    {"id": "q27", "text": "最近、やる気はありますか？", "category": "心身のストレス反応"},
    {"id": "q28", "text": "最近、ストレスを感じますか？", "category": "心身のストレス反応"},
    {"id": "q29", "text": "最近、緊張することがありますか？", "category": "心身のストレス反応"},
    {"id": "q30", "text": "最近、落ち着かないことがありますか？", "category": "心身のストレス反応"},
    {"id": "q31", "text": "最近、心配事はありますか？", "category": "心身のストレス反応"},
    {"id": "q32", "text": "最近、憂鬱な気分になることがありますか？", "category": "心身のストレス反応"},
    {"id": "q33", "text": "最近、悲しい気持ちになることがありますか？", "category": "心身のストレス反応"},
    {"id": "q34", "text": "最近、希望を感じますか？", "category": "心身のストレス反応"},
    {"id": "q35", "text": "最近、楽しみはありますか？", "category": "心身のストレス反応"},
    {"id": "q36", "text": "最近、満足感はありますか？", "category": "心身のストレス反応"},
    {"id": "q37", "text": "最近、達成感はありますか？", "category": "心身のストレス反応"},
    {"id": "q38", "text": "最近、頭痛がすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q39", "text": "最近、肩こりがすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q40", "text": "最近、腰痛がすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q41", "text": "最近、目の疲れを感じますか？", "category": "心身のストレス反応"},
    {"id": "q42", "text": "最近、胃の調子は良いですか？", "category": "心身のストレス反応"},
    {"id": "q43", "text": "最近、めまいがすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q44", "text": "最近、動悸がすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q45", "text": "最近、息切れがすることがありますか？", "category": "心身のストレス反応"},
    {"id": "q46", "text": "最近、手足のしびれを感じますか？", "category": "心身のストレス反応"},
    {"id": "q47", "text": "上司からのサポートはありますか？", "category": "周囲のサポート"},
    {"id": "q48", "text": "上司との関係は良好ですか？", "category": "周囲のサポート"},
    {"id": "q49", "text": "上司からの理解はありますか？", "category": "周囲のサポート"},
    {"id": "q50", "text": "同僚からのサポートはありますか？", "category": "周囲のサポート"},
    {"id": "q51", "text": "同僚との関係は良好ですか？", "category": "周囲のサポート"},
    {"id": "q52", "text": "同僚からの理解はありますか？", "category": "周囲のサポート"},
    {"id": "q53", "text": "家族・友人からのサポートはありますか？", "category": "周囲のサポート"},
    {"id": "q54", "text": "家族・友人との関係は良好ですか？", "category": "周囲のサポート"},
    {"id": "q55", "text": "家族・友人からの理解はありますか？", "category": "周囲のサポート"},
    {"id": "q56", "text": "現在の仕事に満足していますか？", "category": "満足度"},
    {"id": "q57", "text": "現在の生活に満足していますか？", "category": "満足度"}
]


@router.get("/questions")
async def get_questions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """57項目の質問を取得"""
    # 重複チェック: 今月のストレスチェックが既に受検済みか確認
    period = date.today().replace(day=1)
    is_duplicate = await check_duplicate_stress_check(db, str(current_user.id), period)
    
    response = {"questions": STRESS_CHECK_QUESTIONS}
    if is_duplicate:
        response["already_taken"] = True
        response["message"] = "この期間は既に受検済みです。受検できません。"
    
    return response


@router.post("/submit", response_model=StressCheckResult)
async def submit_stress_check(
    answer_data: StressCheckAnswer,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ストレスチェック回答を送信"""
    # バリデーション: 全57項目に回答があるか
    if len(answer_data.answers) != 57:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="全ての質問に回答してください"
        )

    # バリデーション: 回答値が1-4の範囲内か
    for q_id, value in answer_data.answers.items():
        if value < 1 or value > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"有効な回答を選択してください: {q_id}"
            )

    # 実施期間（今月の1日）
    period = date.today().replace(day=1)

    # 重複チェック
    is_duplicate = await check_duplicate_stress_check(db, str(current_user.id), period)
    if is_duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="この期間は既に受検済みです"
        )

    # スコア計算
    scores = calculate_stress_scores(answer_data.answers)
    high_stress = is_high_stress(
        scores["stress_reaction_score"],
        scores["job_stress_score"],
        scores["support_score"]
    )

    # データベースに保存
    stress_check = StressCheck(
        user_id=current_user.id,
        period=period,
        answers=answer_data.answers,
        total_score=scores["total_score"],
        is_high_stress=high_stress
    )
    db.add(stress_check)

    # 途中保存を削除
    draft_result = await db.execute(
        select(DraftAnswer).where(DraftAnswer.user_id == current_user.id)
    )
    draft = draft_result.scalar_one_or_none()
    if draft:
        await db.delete(draft)

    await db.commit()
    await db.refresh(stress_check)

    return StressCheckResult(
        id=str(stress_check.id),
        period=stress_check.period,
        total_score=stress_check.total_score,
        is_high_stress=stress_check.is_high_stress,
        job_stress_score=scores["job_stress_score"],
        stress_reaction_score=scores["stress_reaction_score"],
        support_score=scores["support_score"],
        satisfaction_score=scores["satisfaction_score"]
    )


@router.get("/history", response_model=list[StressCheckHistoryItem])
async def get_stress_check_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ストレスチェック履歴を取得"""
    result = await db.execute(
        select(StressCheck)
        .where(StressCheck.user_id == current_user.id)
        .order_by(StressCheck.period.desc())
    )
    checks = result.scalars().all()

    return [
        StressCheckHistoryItem(
            id=str(check.id),
            period=check.period,
            total_score=check.total_score,
            is_high_stress=check.is_high_stress
        )
        for check in checks
    ]


@router.get("/result/{check_id}", response_model=StressCheckResult)
async def get_stress_check_result(
    check_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ストレスチェック結果を取得"""
    result = await db.execute(
        select(StressCheck).where(
            StressCheck.id == UUID(check_id),
            StressCheck.user_id == current_user.id
        )
    )
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ストレスチェック結果が見つかりません"
        )

    # スコアを再計算
    scores = calculate_stress_scores(check.answers)

    return StressCheckResult(
        id=str(check.id),
        period=check.period,
        total_score=check.total_score,
        is_high_stress=check.is_high_stress,
        job_stress_score=scores["job_stress_score"],
        stress_reaction_score=scores["stress_reaction_score"],
        support_score=scores["support_score"],
        satisfaction_score=scores["satisfaction_score"]
    )


@router.get("/draft", response_model=DraftAnswerResponse)
async def get_draft_answer(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """途中保存された回答を取得"""
    result = await db.execute(
        select(DraftAnswer).where(DraftAnswer.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        return DraftAnswerResponse(answers={})

    return DraftAnswerResponse(
        answers=draft.answers or {},
        updated_at=draft.updated_at.isoformat() if draft.updated_at else None
    )


@router.post("/draft", response_model=DraftAnswerResponse)
async def save_draft_answer(
    data: DraftAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """回答を途中保存"""
    # バリデーション: 回答値が1-4の範囲内か
    for q_id, value in data.answers.items():
        if value < 1 or value > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"有効な回答を選択してください: {q_id}"
            )

    # 既存の途中保存を取得
    result = await db.execute(
        select(DraftAnswer).where(DraftAnswer.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()

    if draft:
        # 更新
        draft.answers = data.answers
    else:
        # 新規作成
        draft = DraftAnswer(
            user_id=current_user.id,
            answers=data.answers
        )
        db.add(draft)

    await db.commit()
    await db.refresh(draft)

    return DraftAnswerResponse(
        answers=draft.answers,
        updated_at=draft.updated_at.isoformat() if draft.updated_at else None
    )


@router.delete("/draft")
async def delete_draft_answer(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """途中保存を削除"""
    result = await db.execute(
        select(DraftAnswer).where(DraftAnswer.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()

    if draft:
        await db.delete(draft)
        await db.commit()

    return {"message": "途中保存を削除しました"}


@router.post("/draft/migrate", response_model=DraftAnswerResponse)
async def migrate_draft_from_localstorage(
    data: MigrateDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """localStorageからの途中保存データを移行"""
    # バリデーション: 回答値が1-4の範囲内か
    for q_id, value in data.answers.items():
        if value < 1 or value > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"有効な回答を選択してください: {q_id}"
            )

    # 既存の途中保存を取得
    result = await db.execute(
        select(DraftAnswer).where(DraftAnswer.user_id == current_user.id)
    )
    draft = result.scalar_one_or_none()

    # サーバー側に既に保存がある場合はスキップ（サーバー側を優先）
    if draft and draft.answers and len(draft.answers) > 0:
        return DraftAnswerResponse(
            answers=draft.answers,
            updated_at=draft.updated_at.isoformat() if draft.updated_at else None
        )

    # localStorageのデータを保存
    if draft:
        draft.answers = data.answers
    else:
        draft = DraftAnswer(
            user_id=current_user.id,
            answers=data.answers
        )
        db.add(draft)

    await db.commit()
    await db.refresh(draft)

    return DraftAnswerResponse(
        answers=draft.answers,
        updated_at=draft.updated_at.isoformat() if draft.updated_at else None
    )


@router.get("/non-taken", response_model=NonTakenUsersResponse)
async def get_non_taken_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    deadline: Optional[date] = Query(None, description="受検期限")
):
    """
    未受検者一覧を取得（管理者専用）
    - 今月のストレスチェックを受けていないユーザーを抽出
    - 各ユーザーの最終受検日も取得
    """
    # 管理者のみアクセス可能
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    # 今月の期間（月初日）
    current_period = date.today().replace(day=1)
    if deadline is None:
        next_month = (current_period.replace(day=28) + timedelta(days=4)).replace(day=1)
        deadline = next_month - timedelta(days=1)

    # 同じ会社の全従業員を取得
    users_result = await db.execute(
        select(User).where(User.company_id == current_user.company_id)
    )
    all_users = users_result.scalars().all()

    # 今月受検済みのユーザーIDを取得
    taken_result = await db.execute(
        select(StressCheck.user_id).where(
            and_(
                StressCheck.period == current_period,
                StressCheck.user_id.in_([u.id for u in all_users])
            )
        )
    )
    taken_user_ids = set(row[0] for row in taken_result.fetchall())

    # 未受検者リストを作成
    non_taken_users = []
    for user in all_users:
        if user.id not in taken_user_ids:
            # 最終受検日を取得
            last_check_result = await db.execute(
                select(StressCheck.period)
                .where(StressCheck.user_id == user.id)
                .order_by(StressCheck.period.desc())
                .limit(1)
            )
            last_check_row = last_check_result.fetchone()
            last_check_date = last_check_row[0] if last_check_row else None

            # メールアドレスからユーザー名を生成
            name = user.email.split('@')[0] if user.email else "Unknown"

            non_taken_users.append(NonTakenUser(
                id=str(user.id),
                email=user.email,
                name=name,
                last_check_date=last_check_date
            ))

    return NonTakenUsersResponse(
        period=current_period,
        deadline=deadline,
        users=non_taken_users,
        total_count=len(all_users),
        non_taken_count=len(non_taken_users)
    )
