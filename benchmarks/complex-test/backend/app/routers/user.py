"""
ユーザー関連エンドポイント（LINE連携など）
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import secrets
import string

from app.db.database import get_db
from app.db.models import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/user", tags=["user"])


class LineLinkCodeResponse(BaseModel):
    """LINE連携コードレスポンス"""
    link_code: str
    instruction: str


class LineStatusResponse(BaseModel):
    """LINE連携状態レスポンス"""
    is_linked: bool
    link_code: Optional[str] = None


def generate_link_code(length: int = 8) -> str:
    """ランダムな連携コードを生成"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.get("/line/status", response_model=LineStatusResponse)
async def get_line_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """LINE連携状態を確認"""
    is_linked = current_user.line_user_id is not None

    return LineStatusResponse(
        is_linked=is_linked,
        link_code=current_user.link_code if not is_linked else None
    )


@router.post("/line/generate-code", response_model=LineLinkCodeResponse)
async def generate_line_link_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """LINE連携コードを生成"""
    # 既に連携済みの場合
    if current_user.line_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既にLINEと連携済みです"
        )

    # 新しい連携コードを生成
    while True:
        new_code = generate_link_code()
        # 重複チェック
        result = await db.execute(
            select(User).where(User.link_code == new_code)
        )
        if not result.scalar_one_or_none():
            break

    # 連携コードを保存
    current_user.link_code = new_code
    await db.commit()

    return LineLinkCodeResponse(
        link_code=new_code,
        instruction=f"LINEで「LINK:{new_code}」と送信してください"
    )


@router.delete("/line/unlink")
async def unlink_line(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """LINE連携を解除"""
    if not current_user.line_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LINEと連携されていません"
        )

    current_user.line_user_id = None
    current_user.link_code = None
    await db.commit()

    return {"message": "LINE連携を解除しました"}
