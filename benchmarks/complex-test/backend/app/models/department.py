"""
部署関連のPydanticモデル
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DepartmentBase(BaseModel):
    """部署の基本情報"""
    name: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """部署作成リクエスト"""
    pass


class DepartmentUpdate(BaseModel):
    """部署更新リクエスト"""
    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    """部署レスポンス"""
    id: str
    company_id: str
    employee_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    """部署一覧レスポンス"""
    departments: List[DepartmentResponse]
    total: int
