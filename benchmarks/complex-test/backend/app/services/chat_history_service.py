"""
チャット履歴サービス（PostgreSQL版）

チャット履歴をPostgreSQLに保存・取得します。
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import uuid as uuid_module

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage


async def save_chat_message(
    db: AsyncSession,
    user_id: UUID,
    role: str,
    content: str,
    sentiment_score: Optional[float] = None
) -> str:
    """
    チャットメッセージをPostgreSQLに保存

    Args:
        db: データベースセッション
        user_id: ユーザーID
        role: メッセージの役割 ("user" または "ai")
        content: メッセージ内容
        sentiment_score: 感情スコア (AI応答の場合のみ)

    Returns:
        保存されたメッセージのID
    """
    message = ChatMessage(
        id=uuid_module.uuid4(),
        user_id=user_id,
        role=role,
        content=content,
        sentiment_score=sentiment_score
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return str(message.id)


async def get_chat_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> List[dict]:
    """
    ユーザーのチャット履歴を取得

    Args:
        db: データベースセッション
        user_id: ユーザーID
        limit: 取得する最大件数
        offset: スキップする件数

    Returns:
        チャットメッセージのリスト
    """
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "sentiment_score": msg.sentiment_score,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in messages
    ]


async def get_chat_history_count(db: AsyncSession, user_id: UUID) -> int:
    """
    ユーザーのチャット履歴の総数を取得

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        チャット履歴の総数
    """
    result = await db.execute(
        select(func.count(ChatMessage.id))
        .where(ChatMessage.user_id == user_id)
    )
    return result.scalar() or 0


async def delete_chat_history(db: AsyncSession, user_id: UUID) -> int:
    """
    ユーザーのチャット履歴を全削除

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        削除されたメッセージ数
    """
    # まず件数を取得
    count = await get_chat_history_count(db, user_id)

    # 削除を実行
    await db.execute(
        delete(ChatMessage).where(ChatMessage.user_id == user_id)
    )
    await db.commit()

    return count


async def delete_chat_message(db: AsyncSession, user_id: UUID, message_id: str) -> bool:
    """
    特定のチャットメッセージを削除

    Args:
        db: データベースセッション
        user_id: ユーザーID
        message_id: メッセージID

    Returns:
        削除成功の場合True
    """
    try:
        message_uuid = UUID(message_id)
    except ValueError:
        return False

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.id == message_uuid, ChatMessage.user_id == user_id)
    )
    message = result.scalar_one_or_none()

    if message is None:
        return False

    await db.delete(message)
    await db.commit()
    return True
