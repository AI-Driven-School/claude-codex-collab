"""
チャット関連のPydanticモデル
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """チャットメッセージ"""
    content: str
    timestamp: Optional[datetime] = None


class ChatResponse(BaseModel):
    """チャットレスポンス"""
    message: str
    sentiment_score: float
    topics: List[str]
    urgency: int
    risk_flags: List[str]


class DailyScoreResponse(BaseModel):
    """日次スコアレスポンス"""
    date: str
    sentiment_score: float
    fatigue_level: Optional[int] = None
    sleep_hours: Optional[float] = None
    risk_level: str  # "low" | "medium" | "high"


# チャット履歴用モデル
class ChatHistoryMessage(BaseModel):
    """チャット履歴メッセージ"""
    id: str
    role: str  # "user" | "ai"
    content: str
    sentiment_score: Optional[float] = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    """チャット履歴レスポンス"""
    messages: List[ChatHistoryMessage]
    total: int
    limit: int
    offset: int


class SaveChatMessageRequest(BaseModel):
    """チャットメッセージ保存リクエスト"""
    role: str  # "user" | "ai"
    content: str
    sentiment_score: Optional[float] = None


class SaveChatMessageResponse(BaseModel):
    """チャットメッセージ保存レスポンス"""
    id: str
    success: bool


class DeleteChatHistoryResponse(BaseModel):
    """チャット履歴削除レスポンス"""
    deleted_count: int
    success: bool
