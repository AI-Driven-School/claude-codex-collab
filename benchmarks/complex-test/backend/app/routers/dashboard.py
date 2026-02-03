"""
ダッシュボード関連エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.database import get_db
from app.db.models import User, StressCheck, DailyScore, UserRole, Department
from app.models.dashboard import DashboardResponse, DashboardStats, DepartmentStat, AlertItem, RecommendationItem
from app.routers.auth import get_current_user
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from enum import Enum

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


class PeriodFilter(str, Enum):
    """期間フィルターの種類"""
    THIS_MONTH = "thisMonth"
    LAST_MONTH = "lastMonth"
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"
    ONE_YEAR = "1year"
    ALL = "all"


def get_date_range_from_period(period: Optional[PeriodFilter]) -> tuple[Optional[date], Optional[date]]:
    """期間フィルターから日付範囲を計算"""
    if period is None or period == PeriodFilter.ALL:
        return None, None

    today = date.today()
    end_date = today

    if period == PeriodFilter.THIS_MONTH:
        start_date = today.replace(day=1)
    elif period == PeriodFilter.LAST_MONTH:
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        start_date = last_month_end.replace(day=1)
        end_date = last_month_end
    elif period == PeriodFilter.THREE_MONTHS:
        start_date = today - timedelta(days=90)
    elif period == PeriodFilter.SIX_MONTHS:
        start_date = today - timedelta(days=180)
    elif period == PeriodFilter.ONE_YEAR:
        start_date = today - timedelta(days=365)
    else:
        return None, None

    return start_date, end_date


@router.get("/company/{company_id}", response_model=DashboardResponse)
async def get_company_dashboard(
    company_id: str,
    department_id: Optional[str] = Query(None, description="部署IDでフィルタリング"),
    period: Optional[PeriodFilter] = Query(None, description="期間フィルター"),
    start_date: Optional[date] = Query(None, description="開始日（YYYY-MM-DD形式）"),
    end_date: Optional[date] = Query(None, description="終了日（YYYY-MM-DD形式）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """会社全体の統計データ取得（部署・期間フィルター対応）"""
    # 管理者のみアクセス可能
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    # company_idがリクエストユーザーの所属企業と一致するか検証
    if str(current_user.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他企業のデータにはアクセスできません"
        )

    # 会社のユーザー一覧を取得（部署フィルターあり）
    query = select(User).where(User.company_id == UUID(company_id))
    if department_id:
        query = query.where(User.department_id == UUID(department_id))

    users_result = await db.execute(query)
    users = users_result.scalars().all()

    if not users:
        # データがない場合のデフォルト値
        return DashboardResponse(
            stats=DashboardStats(
                total_employees=0,
                high_stress_count=0,
                stress_check_completion_rate=0.0,
                average_stress_score=0.0
            ),
            department_stats=[],
            alerts=[],
            recommendations=[]
        )

    # 統計計算
    total_employees = len(users)
    user_ids = [user.id for user in users]

    # 日付範囲の決定（カスタム日付 > period > 全期間）
    if start_date is not None or end_date is not None:
        filter_start_date = start_date
        filter_end_date = end_date or date.today()
    else:
        filter_start_date, filter_end_date = get_date_range_from_period(period)

    # 日付フィルター条件を構築
    date_conditions = []
    if filter_start_date is not None:
        date_conditions.append(StressCheck.created_at >= filter_start_date)
    if filter_end_date is not None:
        date_conditions.append(StressCheck.created_at < filter_end_date + timedelta(days=1))

    # 高ストレス者数
    high_stress_result = await db.execute(
        select(func.count(StressCheck.id))
        .where(
            and_(
                StressCheck.user_id.in_(user_ids),
                StressCheck.is_high_stress == True,
                *date_conditions
            )
        )
    )
    high_stress_count = high_stress_result.scalar() or 0

    # ストレスチェック受検率
    total_checks_result = await db.execute(
        select(func.count(func.distinct(StressCheck.user_id)))
        .where(
            and_(
                StressCheck.user_id.in_(user_ids),
                *date_conditions
            )
        )
    )
    users_with_checks = total_checks_result.scalar() or 0
    completion_rate = (users_with_checks / total_employees * 100) if total_employees > 0 else 0.0

    # 平均ストレススコア
    avg_score_result = await db.execute(
        select(func.avg(StressCheck.total_score))
        .where(
            and_(
                StressCheck.user_id.in_(user_ids),
                *date_conditions
            )
        )
    )
    average_stress_score = avg_score_result.scalar() or 0.0

    # 部署別統計を実データから取得
    department_stats = await get_department_stats(db, UUID(company_id))

    # アラート（簡易実装）
    alerts = []
    if high_stress_count > 0:
        alerts.append(AlertItem(
            id="alert-1",
            department_name="全体",
            alert_level="high" if high_stress_count > total_employees * 0.2 else "medium",
            message=f"高ストレス者が{high_stress_count}名検出されました",
            created_at=date.today()
        ))

    # AI改善提案を生成
    from app.services.ai_service import generate_improvement_recommendations

    # 部署統計をdict形式に変換
    dept_stats_dict = [
        {
            "department_name": dept.department_name,
            "average_score": dept.average_score,
            "high_stress_count": dept.high_stress_count,
            "employee_count": dept.employee_count
        }
        for dept in department_stats
    ]

    # 全体統計
    overall_stats = {
        "total_employees": total_employees,
        "high_stress_count": high_stress_count,
        "average_stress_score": float(average_stress_score),
        "stress_check_completion_rate": completion_rate
    }

    # AI提案を生成
    ai_recommendations = await generate_improvement_recommendations(
        dept_stats_dict,
        overall_stats
    )

    # RecommendationItemに変換
    recommendations = [
        RecommendationItem(
            id=rec.get("id", f"rec-{idx}"),
            title=rec.get("title", "改善提案"),
            description=rec.get("description", ""),
            department_name=rec.get("department_name"),
            priority=rec.get("priority", "medium")
        )
        for idx, rec in enumerate(ai_recommendations)
    ]

    return DashboardResponse(
        stats=DashboardStats(
            total_employees=total_employees,
            high_stress_count=high_stress_count,
            stress_check_completion_rate=completion_rate,
            average_stress_score=float(average_stress_score)
        ),
        department_stats=department_stats,
        alerts=alerts,
        recommendations=recommendations
    )


@router.get("/alerts", response_model=list[AlertItem])
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """高ストレスアラート一覧取得"""
    # 管理者のみアクセス可能
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    from app.services.alert_service import get_alerts_for_company
    alerts = await get_alerts_for_company(db, current_user.company_id)
    return alerts


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """アラートを既読にする"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    from app.services.alert_service import mark_alert_as_read
    mark_alert_as_read(alert_id)
    return {"status": "ok", "alert_id": alert_id}


@router.delete("/alerts/{alert_id}/read")
async def mark_alert_unread(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """アラートを未読に戻す"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    from app.services.alert_service import mark_alert_as_unread
    mark_alert_as_unread(alert_id)
    return {"status": "ok", "alert_id": alert_id}


async def get_department_stats(db: AsyncSession, company_id: UUID) -> list[DepartmentStat]:
    """
    部署別統計を取得（N+1クエリ対策済み）
    単一のサブクエリで全部署の統計を一括取得
    """
    from sqlalchemy import literal_column, case
    from sqlalchemy.orm import aliased

    # サブクエリ: 部署ごとの従業員数
    employee_count_subq = (
        select(
            User.department_id,
            func.count(User.id).label("employee_count")
        )
        .where(User.company_id == company_id)
        .group_by(User.department_id)
        .subquery()
    )

    # サブクエリ: 部署ごとのストレスチェック統計
    stress_stats_subq = (
        select(
            User.department_id,
            func.avg(StressCheck.total_score).label("avg_score"),
            func.count(
                case((StressCheck.is_high_stress == True, 1))
            ).label("high_stress_count")
        )
        .join(StressCheck, StressCheck.user_id == User.id)
        .where(User.company_id == company_id)
        .group_by(User.department_id)
        .subquery()
    )

    # メインクエリ: 部署情報と統計を結合
    result = await db.execute(
        select(
            Department.name,
            func.coalesce(employee_count_subq.c.employee_count, 0).label("employee_count"),
            func.coalesce(stress_stats_subq.c.avg_score, 0.0).label("avg_score"),
            func.coalesce(stress_stats_subq.c.high_stress_count, 0).label("high_stress_count")
        )
        .outerjoin(employee_count_subq, Department.id == employee_count_subq.c.department_id)
        .outerjoin(stress_stats_subq, Department.id == stress_stats_subq.c.department_id)
        .where(Department.company_id == company_id)
    )

    department_stats = []
    for row in result.fetchall():
        if row.employee_count == 0:
            continue

        department_stats.append(DepartmentStat(
            department_name=row.name,
            average_score=float(row.avg_score) if row.avg_score else 0.0,
            high_stress_count=int(row.high_stress_count) if row.high_stress_count else 0,
            employee_count=int(row.employee_count)
        ))

    return department_stats
