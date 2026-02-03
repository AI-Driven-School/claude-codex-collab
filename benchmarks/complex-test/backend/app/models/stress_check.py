"""
ストレスチェック関連のPydanticモデル
"""
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date


class StressCheckAnswer(BaseModel):
    """ストレスチェック回答リクエスト"""
    answers: Dict[str, int]  # { "q1": 4, "q2": 2, ... }


class StressCheckQuestion(BaseModel):
    """ストレスチェック質問"""
    id: str
    text: str
    category: str


class StressCheckResult(BaseModel):
    """ストレスチェック結果"""
    id: str
    period: date
    total_score: int
    is_high_stress: bool
    job_stress_score: float
    stress_reaction_score: float
    support_score: float
    satisfaction_score: float


class StressCheckHistoryItem(BaseModel):
    """ストレスチェック履歴アイテム"""
    id: str
    period: date
    total_score: int
    is_high_stress: bool


class NonTakenUser(BaseModel):
    """未受検者情報"""
    id: str
    email: str
    name: str  # メールアドレスのローカル部分を使用
    last_check_date: Optional[date]  # 最終受検日


class NonTakenUsersResponse(BaseModel):
    """未受検者一覧レスポンス"""
    period: date  # 対象期間
    deadline: Optional[date]  # 受検期限
    users: list[NonTakenUser]
    total_count: int  # 全従業員数
    non_taken_count: int  # 未受検者数


class DraftAnswerRequest(BaseModel):
    """途中保存リクエスト"""
    answers: Dict[str, int]  # { "q1": 4, "q2": 2, ... }


class DraftAnswerResponse(BaseModel):
    """途中保存レスポンス"""
    answers: Dict[str, int]
    updated_at: Optional[str] = None


class MigrateDraftRequest(BaseModel):
    """localStorage移行リクエスト"""
    answers: Dict[str, int]
