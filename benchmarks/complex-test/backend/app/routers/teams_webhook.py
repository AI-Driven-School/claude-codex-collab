"""
Microsoft Teams Webhook通知APIエンドポイント

管理者向けのTeams通知送信APIを提供します。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.db.models import User
from app.routers.auth import get_current_user
from app.services.teams_service import teams_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


class ReminderRequest(BaseModel):
    """リマインダー送信リクエスト"""
    pending_count: int
    period: str
    deadline: Optional[str] = None


class AlertRequest(BaseModel):
    """アラート送信リクエスト"""
    department: Optional[str] = None
    alert_count: int = 1
    urgency_level: int = 1


class CompletionRequest(BaseModel):
    """完了通知送信リクエスト"""
    period: str
    total_count: int
    completed_count: int
    completion_rate: float


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """管理者権限を要求"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user


@router.post("/send-reminder")
async def send_reminder(
    request: ReminderRequest,
    current_user: User = Depends(require_admin)
):
    """
    ストレスチェックリマインダーをTeamsに送信

    - 管理者のみ実行可能
    - pending_count: 未受検者数
    - period: 対象期間（例: 2024年1月）
    - deadline: 締め切り日（オプション）
    """
    if not teams_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Teams連携が設定されていません"
        )

    success = await teams_service.send_stress_check_reminder(
        pending_count=request.pending_count,
        period=request.period,
        deadline=request.deadline
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Teamsへの通知送信に失敗しました"
        )

    return {"success": True, "message": "リマインダーを送信しました"}


@router.post("/send-alert")
async def send_alert(
    request: AlertRequest,
    current_user: User = Depends(require_admin)
):
    """
    高ストレスアラートをTeamsに送信

    - 管理者のみ実行可能
    - department: 対象部署（オプション）
    - alert_count: アラート対象者数
    - urgency_level: 緊急度レベル（1-3）
    """
    if not teams_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Teams連携が設定されていません"
        )

    if request.urgency_level < 1 or request.urgency_level > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="urgency_levelは1から3の間で指定してください"
        )

    success = await teams_service.send_high_stress_alert(
        department=request.department,
        alert_count=request.alert_count,
        urgency_level=request.urgency_level
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Teamsへの通知送信に失敗しました"
        )

    return {"success": True, "message": "アラートを送信しました"}


@router.post("/send-completion")
async def send_completion(
    request: CompletionRequest,
    current_user: User = Depends(require_admin)
):
    """
    ストレスチェック完了通知をTeamsに送信

    - 管理者のみ実行可能
    - period: 対象期間
    - total_count: 対象者総数
    - completed_count: 受検完了者数
    - completion_rate: 受検率（0.0-1.0）
    """
    if not teams_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Teams連携が設定されていません"
        )

    if request.completion_rate < 0 or request.completion_rate > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="completion_rateは0から1の間で指定してください"
        )

    success = await teams_service.send_completion_notification(
        period=request.period,
        total_count=request.total_count,
        completed_count=request.completed_count,
        completion_rate=request.completion_rate
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Teamsへの通知送信に失敗しました"
        )

    return {"success": True, "message": "完了通知を送信しました"}


@router.post("/test")
async def test_teams_connection(
    current_user: User = Depends(require_admin)
):
    """
    Teams連携のテスト通知を送信

    - 管理者のみ実行可能
    - 設定確認用のテストメッセージを送信
    """
    if not teams_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Teams連携が設定されていません。TEAMS_WEBHOOK_URLを設定してください。"
        )

    success = await teams_service.send_test_message()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Teamsへのテスト通知送信に失敗しました"
        )

    return {"success": True, "message": "テスト通知を送信しました"}


@router.get("/status")
async def get_teams_status(
    current_user: User = Depends(require_admin)
):
    """
    Teams連携の設定状態を確認

    - 管理者のみ実行可能
    """
    return {
        "configured": teams_service.is_configured(),
        "message": "Teams連携は設定済みです" if teams_service.is_configured() else "Teams連携は未設定です"
    }
