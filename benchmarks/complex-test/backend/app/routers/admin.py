"""
管理者用ルーター

メール送信、ユーザー管理などの管理者向け機能を提供
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import date
from uuid import UUID

from app.db.database import get_db
from app.db.models import User, StressCheck, UserRole
from app.models.email import (
    ReminderEmailRequest,
    HighStressFollowupEmailRequest,
    CompletionEmailRequest,
    BulkReminderEmailRequest,
    EmailResponse,
    BulkEmailResponse,
)
from app.services.email_service import email_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """管理者権限チェック"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user


@router.post("/email/reminder", response_model=EmailResponse)
async def send_reminder_email(
    request: ReminderEmailRequest,
    current_user: User = Depends(require_admin),
):
    """
    リマインドメール送信（単一）

    未受検者に対してストレスチェックの受検を促すメールを送信
    """
    success = await email_service.send_reminder_email(
        to_email=request.to_email,
        employee_name=request.employee_name,
        company_name=request.company_name,
        deadline=request.deadline,
        check_url=request.check_url,
    )

    if success:
        return EmailResponse(
            success=True,
            message="リマインドメールを送信しました",
            email=request.to_email
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メール送信に失敗しました"
        )


@router.post("/email/reminder/bulk", response_model=BulkEmailResponse)
async def send_bulk_reminder_emails(
    request: BulkReminderEmailRequest,
    current_user: User = Depends(require_admin),
):
    """
    リマインドメール一括送信

    複数の未受検者に対してストレスチェックの受検を促すメールを一括送信
    """
    results = {}
    success_count = 0
    failed_count = 0

    for recipient in request.recipients:
        email = recipient.get("email")
        name = recipient.get("name", "従業員")

        if not email:
            continue

        success = await email_service.send_reminder_email(
            to_email=email,
            employee_name=name,
            company_name=request.company_name,
            deadline=request.deadline,
            check_url=request.check_url,
        )

        results[email] = success
        if success:
            success_count += 1
        else:
            failed_count += 1

    return BulkEmailResponse(
        total=len(request.recipients),
        success_count=success_count,
        failed_count=failed_count,
        results=results
    )


@router.post("/email/high-stress-followup", response_model=EmailResponse)
async def send_high_stress_followup_email(
    request: HighStressFollowupEmailRequest,
    current_user: User = Depends(require_admin),
):
    """
    高ストレス者フォローアップメール送信

    高ストレス者に対してサポート情報を含むメールを送信
    """
    success = await email_service.send_high_stress_followup_email(
        to_email=request.to_email,
        employee_name=request.employee_name,
        company_name=request.company_name,
        consultation_url=request.consultation_url,
        support_email=request.support_email,
    )

    if success:
        return EmailResponse(
            success=True,
            message="フォローアップメールを送信しました",
            email=request.to_email
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メール送信に失敗しました"
        )


@router.post("/email/completion", response_model=EmailResponse)
async def send_completion_email(
    request: CompletionEmailRequest,
    current_user: User = Depends(require_admin),
):
    """
    ストレスチェック完了通知メール送信

    ストレスチェック完了後に結果確認URLを含むメールを送信
    """
    success = await email_service.send_completion_notification_email(
        to_email=request.to_email,
        employee_name=request.employee_name,
        company_name=request.company_name,
        check_date=request.check_date,
        result_url=request.result_url,
        is_high_stress=request.is_high_stress,
    )

    if success:
        return EmailResponse(
            success=True,
            message="完了通知メールを送信しました",
            email=request.to_email
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メール送信に失敗しました"
        )


@router.get("/users/incomplete/{period}")
async def get_incomplete_users(
    period: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    未受検者一覧取得

    指定期間のストレスチェックを未受検のユーザー一覧を取得
    """
    # 現在の会社の全ユーザーを取得
    all_users_result = await db.execute(
        select(User).where(User.company_id == current_user.company_id)
    )
    all_users = all_users_result.scalars().all()

    # 指定期間に受検済みのユーザーIDを取得
    completed_result = await db.execute(
        select(StressCheck.user_id).where(StressCheck.period == period)
    )
    completed_user_ids = {row[0] for row in completed_result.fetchall()}

    # 未受検ユーザーをフィルタリング
    incomplete_users = [
        {
            "id": str(user.id),
            "email": user.email,
            "name": user.email.split("@")[0],  # 仮の名前
        }
        for user in all_users
        if user.id not in completed_user_ids and user.role == "employee"
    ]

    return {
        "period": period.isoformat(),
        "total_employees": len([u for u in all_users if u.role == "employee"]),
        "incomplete_count": len(incomplete_users),
        "users": incomplete_users
    }


@router.get("/users/high-stress/{period}")
async def get_high_stress_users(
    period: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    高ストレス者一覧取得

    指定期間のストレスチェックで高ストレスと判定されたユーザー一覧を取得
    """
    result = await db.execute(
        select(StressCheck, User)
        .join(User, StressCheck.user_id == User.id)
        .where(
            and_(
                StressCheck.period == period,
                StressCheck.is_high_stress == True,
                User.company_id == current_user.company_id
            )
        )
    )

    high_stress_users = [
        {
            "id": str(user.id),
            "email": user.email,
            "name": user.email.split("@")[0],
            "check_date": stress_check.created_at.date().isoformat(),
            "total_score": stress_check.total_score,
        }
        for stress_check, user in result.fetchall()
    ]

    return {
        "period": period.isoformat(),
        "high_stress_count": len(high_stress_users),
        "users": high_stress_users
    }
