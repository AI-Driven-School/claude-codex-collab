"""
チャット・AI分析関連エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import User, DailyScore
from app.models.chat import (
    ChatMessage,
    ChatResponse,
    DailyScoreResponse,
    ChatHistoryMessage,
    ChatHistoryResponse,
    SaveChatMessageRequest,
    SaveChatMessageResponse,
    DeleteChatHistoryResponse
)
from app.services.ai_service import analyze_sentiment, generate_chat_reply
from app.services.chat_history_service import (
    save_chat_message as save_chat_message_db,
    get_chat_history as get_chat_history_db,
    get_chat_history_count as get_chat_history_count_db,
    delete_chat_history as delete_chat_history_db,
    delete_chat_message as delete_chat_message_db
)
from app.routers.auth import get_current_user
from app.services.notification_service import (
    get_notification_service,
    check_and_notify_high_stress,
    NotificationPayload,
    NotificationType
)
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, and_, func
from uuid import UUID
from collections import defaultdict

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットメッセージを送信"""
    # バリデーション: メッセージが空でないか
    if not message.content or len(message.content.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="メッセージを入力してください"
        )

    # バリデーション: 文字数制限
    if len(message.content) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="メッセージは1000文字以内で入力してください"
        )

    # レート制限チェック: 過去1時間のメッセージ数を確認
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_scores_result = await db.execute(
        select(func.count(DailyScore.id))
        .where(
            and_(
                DailyScore.user_id == current_user.id,
                DailyScore.created_at >= one_hour_ago
            )
        )
    )
    recent_count = recent_scores_result.scalar() or 0

    if recent_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="送信回数の上限に達しました"
        )

    # AI分析
    analysis = await analyze_sentiment(message.content)

    # 不適切なコンテンツが検出された場合
    if "inappropriate_content" in analysis.get("risk_flags", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不適切な内容が検出されました"
        )

    # 日次スコアを保存
    today = date.today()
    daily_score = DailyScore(
        user_id=current_user.id,
        date=today,
        sentiment_score=analysis["sentiment"],
        fatigue_level=None,  # AI分析から推測可能な場合は設定
        sleep_hours=None
    )
    db.add(daily_score)
    await db.commit()

    # AI返信を生成
    reply = await generate_chat_reply(message.content)

    # 高ストレス検出時の自動通知
    await check_and_notify_high_stress(
        sentiment_score=analysis["sentiment"],
        urgency=analysis["urgency"],
        risk_flags=analysis["risk_flags"],
        topics=analysis["topics"]
    )

    return ChatResponse(
        message=reply,
        sentiment_score=analysis["sentiment"],
        topics=analysis["topics"],
        urgency=analysis["urgency"],
        risk_flags=analysis["risk_flags"]
    )


@router.get("/daily-scores", response_model=list[DailyScoreResponse])
async def get_daily_scores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """日次スコアを取得"""
    result = await db.execute(
        select(DailyScore)
        .where(DailyScore.user_id == current_user.id)
        .order_by(DailyScore.date.desc())
        .limit(30)  # 過去30日分
    )
    scores = result.scalars().all()

    return [
        DailyScoreResponse(
            date=str(score.date),
            sentiment_score=score.sentiment_score,
            fatigue_level=score.fatigue_level,
            sleep_hours=score.sleep_hours,
            risk_level="high" if score.sentiment_score < -0.5 else "medium" if score.sentiment_score < 0 else "low"
        )
        for score in scores
    ]


# ===== チャット履歴API（MongoDB） =====

@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャット履歴を取得"""
    messages = await get_chat_history_db(db, current_user.id, limit=limit, offset=offset)
    total = await get_chat_history_count_db(db, current_user.id)

    return ChatHistoryResponse(
        messages=[ChatHistoryMessage(**msg) for msg in messages],
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/history", response_model=SaveChatMessageResponse)
async def save_message(
    request: SaveChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットメッセージを保存"""
    # バリデーション: roleの値
    if request.role not in ["user", "ai"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="roleは'user'または'ai'である必要があります"
        )

    # バリデーション: contentが空でない
    if not request.content or len(request.content.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="メッセージ内容が空です"
        )

    message_id = await save_chat_message_db(
        db=db,
        user_id=current_user.id,
        role=request.role,
        content=request.content,
        sentiment_score=request.sentiment_score
    )

    return SaveChatMessageResponse(id=message_id, success=True)


@router.delete("/history", response_model=DeleteChatHistoryResponse)
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャット履歴を全削除"""
    deleted_count = await delete_chat_history_db(db, current_user.id)
    return DeleteChatHistoryResponse(deleted_count=deleted_count, success=True)


@router.delete("/history/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """特定のチャットメッセージを削除"""
    success = await delete_chat_message_db(db, current_user.id, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="メッセージが見つかりません"
        )
    return {"success": True}


class SlackWebhookRequest(BaseModel):
    """Slackからのイベントペイロード"""
    type: str
    challenge: Optional[str] = None
    event: Optional[dict] = None


class TeamsWebhookRequest(BaseModel):
    """Teamsからのイベントペイロード"""
    type: str
    text: Optional[str] = None
    from_user: Optional[dict] = None


@router.post("/webhook/slack")
async def slack_webhook(request: SlackWebhookRequest):
    """SlackからのWebhook受け口"""
    # URL検証チャレンジへの応答
    if request.type == "url_verification":
        return {"challenge": request.challenge}

    # イベント処理
    if request.type == "event_callback" and request.event:
        event_type = request.event.get("type")
        if event_type == "message":
            return {"status": "received", "event_type": event_type}

    return {"status": "ok"}


@router.post("/webhook/teams")
async def teams_webhook(request: TeamsWebhookRequest):
    """Microsoft TeamsからのWebhook受け口"""
    if request.type == "message" and request.text:
        return {"type": "message", "text": "メッセージを受信しました"}

    return {"status": "ok"}


@router.post("/notify/test")
async def test_notification(
    current_user: User = Depends(get_current_user)
):
    """通知テスト用エンドポイント（管理者のみ）"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    service = get_notification_service()
    payload = NotificationPayload(
        notification_type=NotificationType.SYSTEM_NOTIFICATION,
        title="テスト通知",
        message="これはテスト通知です。Slack/Teams連携が正常に動作しています。",
        urgency_level=1
    )
    results = await service.send_notification(payload)

    return {
        "message": "テスト通知を送信しました",
        "results": results
    }
