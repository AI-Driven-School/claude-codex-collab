"""
組織分析AI エンドポイント
部署全体のストレス傾向をAIが分析し、インサイトを生成
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models import User, StressCheck, Department, UserRole
from app.routers.auth import get_current_user
from app.services.org_analysis_service import OrgAnalysisService
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
import os

router = APIRouter(prefix="/api/v1/admin/org-analysis", tags=["org-analysis"])


# --- Pydantic Models ---

class DepartmentScore(BaseModel):
    id: str
    name: str
    score: float
    employee_count: int
    risk_level: Literal["low", "medium", "high"]


class TrendData(BaseModel):
    month: str
    score: float


class AIInsights(BaseModel):
    summary: str
    risk_factors: List[str]
    recommendations: List[str]


class OrgAnalysisResponse(BaseModel):
    organization_score: float
    score_change: float
    total_employees: int
    response_rate: float
    departments: List[DepartmentScore]
    trends: List[TrendData]
    ai_insights: AIInsights
    generated_at: datetime


class ReportGenerationResponse(BaseModel):
    report_url: str
    generated_at: datetime


class DepartmentDetailResponse(BaseModel):
    department: DepartmentScore
    monthly_scores: List[TrendData]
    stress_factors: List[dict]
    high_risk_count: int
    ai_analysis: str


# --- Helper Functions ---

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """管理者権限を要求"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user


# --- Endpoints ---

@router.get("", response_model=OrgAnalysisResponse)
async def get_org_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織全体の分析データを取得
    - 部署別ストレススコア
    - トレンドデータ
    - AIインサイト
    """
    service = OrgAnalysisService(db)
    return await service.get_org_analysis()


@router.post("/generate-report", response_model=ReportGenerationResponse)
async def generate_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    組織分析PDFレポートを生成
    """
    service = OrgAnalysisService(db)
    report_path = await service.generate_pdf_report()

    return ReportGenerationResponse(
        report_url=f"/api/v1/admin/org-analysis/reports/{os.path.basename(report_path)}",
        generated_at=datetime.utcnow()
    )


@router.get("/reports/{filename}")
async def download_report(
    filename: str,
    current_user: User = Depends(require_admin)
):
    """
    生成されたレポートをダウンロード
    """
    report_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
    report_path = os.path.join(report_dir, filename)

    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません"
        )

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get("/department/{department_id}", response_model=DepartmentDetailResponse)
async def get_department_detail(
    department_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    特定部署の詳細分析データを取得
    """
    service = OrgAnalysisService(db)
    return await service.get_department_detail(department_id)
