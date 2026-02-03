"""
ユーザー関連のPydanticモデル
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    id: str
    email: str
    role: str
    company_id: str
    company_name: Optional[str] = None
