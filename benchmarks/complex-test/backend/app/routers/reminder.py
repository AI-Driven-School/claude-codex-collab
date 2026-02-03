"""
リマインダー管理エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from app.db.database import get_db
from app.db.models import User, UserRole
from app.routers.auth import get_current_user
from app.services.reminder_service import reminder_service
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


class ScheduledJobResponse(BaseModel):
    """スケジュールされたジョブのレスポンス"""
    id: str
    name: str
    next_run_time: Optional[str]


class ReminderStatsResponse(BaseModel):
    """リマインダー送信結果のレスポンス"""
    sent: int
    failed: int
    total: int


class NonTakenUserInfo(BaseModel):
    """未受検者情報"""
    id: str
    email: str
    line_linked: bool


class NonTakenUsersPreviewResponse(BaseModel):
    """未受検者プレビューレスポンス"""
    users: List[NonTakenUserInfo]
    total: int
    period: date


@router.get("/jobs", response_model=List[ScheduledJobResponse])
async def get_scheduled_jobs(
    current_user: User = Depends(get_current_user)
):
    """
    スケジュールされているリマインダージョブ一覧を取得
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    jobs = scheduler_service.get_jobs()
    return jobs


@router.post("/trigger", response_model=ReminderStatsResponse)
async def trigger_reminder(
    current_user: User = Depends(get_current_user)
):
    """
    リマインダーを即時実行（管理者専用）
    全企業の未受検者に対してリマインダーを送信します
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    stats = await scheduler_service.trigger_reminder_now()
    return ReminderStatsResponse(**stats)


@router.post("/send/{company_id}", response_model=ReminderStatsResponse)
async def send_reminder_to_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    特定の企業の未受検者にリマインダーを送信（管理者専用）
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    # 同じ会社の管理者かチェック
    if str(current_user.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="自社のリマインダーのみ送信できます"
        )

    users = await reminder_service.get_non_taken_users_with_line(db, company_id)
    stats = await reminder_service.send_reminder_to_users(users)

    return ReminderStatsResponse(**stats)


@router.get("/preview", response_model=NonTakenUsersPreviewResponse)
async def preview_reminder_targets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    リマインダー送信対象の未受検者をプレビュー（管理者専用）
    自社のLINE連携済み未受検者を表示します
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    users = await reminder_service.get_non_taken_users_with_line(
        db,
        str(current_user.company_id)
    )

    user_infos = [
        NonTakenUserInfo(
            id=str(u.id),
            email=u.email,
            line_linked=bool(u.line_user_id)
        )
        for u in users
    ]

    return NonTakenUsersPreviewResponse(
        users=user_infos,
        total=len(user_infos),
        period=date.today().replace(day=1)
    )
