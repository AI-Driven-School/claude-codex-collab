"""
ダッシュボード関連のPydanticモデル
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class DashboardStats(BaseModel):
    """ダッシュボード統計"""
    total_employees: int
    high_stress_count: int
    stress_check_completion_rate: float
    average_stress_score: float


class DepartmentStat(BaseModel):
    """部署別統計"""
    department_name: str
    average_score: float
    high_stress_count: int
    employee_count: int


class AlertItem(BaseModel):
    """アラートアイテム"""
    id: str
    department_name: str
    alert_level: str  # "low" | "medium" | "high"
    message: str
    created_at: date


class RecommendationItem(BaseModel):
    """AI改善提案"""
    id: str
    title: str
    description: str
    department_name: Optional[str] = None
    priority: str  # "low" | "medium" | "high"


class DashboardResponse(BaseModel):
    """ダッシュボードレスポンス"""
    stats: DashboardStats
    department_stats: List[DepartmentStat]
    alerts: List[AlertItem]
    recommendations: List[RecommendationItem]
