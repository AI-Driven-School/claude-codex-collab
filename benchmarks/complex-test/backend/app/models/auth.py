"""
認証関連のPydanticモデル
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    """ユーザー登録リクエスト"""
    company_name: str
    industry: Optional[str] = None
    plan_type: str = "basic"
    email: EmailStr
    password: str
    password_confirm: str


class UserLogin(BaseModel):
    """ログインリクエスト"""
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    """認証ユーザー情報"""
    id: str
    email: EmailStr
    role: str
    company_id: str


class AuthResponse(BaseModel):
    """認証レスポンス"""
    user: AuthUser


class TokenData(BaseModel):
    """トークンデータ"""
    user_id: Optional[str] = None
    role: Optional[str] = None
