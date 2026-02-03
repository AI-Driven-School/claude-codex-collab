"""
メール関連のPydanticモデル
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date
from enum import Enum


class EmailType(str, Enum):
    """メールタイプ"""
    REMINDER = "reminder"
    HIGH_STRESS_FOLLOWUP = "high_stress_followup"
    COMPLETION = "completion"


class ReminderEmailRequest(BaseModel):
    """リマインドメール送信リクエスト"""
    to_email: EmailStr
    employee_name: str
    company_name: str
    deadline: date
    check_url: str


class HighStressFollowupEmailRequest(BaseModel):
    """高ストレス者フォローアップメール送信リクエスト"""
    to_email: EmailStr
    employee_name: str
    company_name: str
    consultation_url: str
    support_email: EmailStr


class CompletionEmailRequest(BaseModel):
    """ストレスチェック完了通知メール送信リクエスト"""
    to_email: EmailStr
    employee_name: str
    company_name: str
    check_date: date
    result_url: str
    is_high_stress: bool = False


class BulkReminderEmailRequest(BaseModel):
    """一括リマインドメール送信リクエスト"""
    company_name: str
    deadline: date
    check_url: str
    recipients: List[dict]  # [{"email": "...", "name": "..."}]


class EmailResponse(BaseModel):
    """メール送信レスポンス"""
    success: bool
    message: str
    email: Optional[str] = None


class BulkEmailResponse(BaseModel):
    """一括メール送信レスポンス"""
    total: int
    success_count: int
    failed_count: int
    results: dict  # {"email": True/False, ...}
