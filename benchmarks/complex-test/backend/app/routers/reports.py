"""
PDFレポート生成エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date
from uuid import UUID

from app.db.database import get_db
from app.db.models import User, StressCheck, Company, UserRole, Department
from app.routers.auth import get_current_user
from app.services.stress_check_service import calculate_stress_scores
from app.services.pdf_generator import (
    get_stress_check_pdf_generator,
    get_group_analysis_pdf_generator,
    get_department_report_pdf_generator
)
from app.services.ai_service import generate_improvement_recommendations

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


async def _get_latest_period(db: AsyncSession, user_ids: list[UUID]) -> date | None:
    if not user_ids:
        return None
    latest_period_result = await db.execute(
        select(func.max(StressCheck.period)).where(StressCheck.user_id.in_(user_ids))
    )
    return latest_period_result.scalar()


async def _get_department_stats_for_period(
    db: AsyncSession,
    company_id: UUID,
    period: date
) -> list[dict]:
    dept_result = await db.execute(
        select(Department).where(Department.company_id == company_id)
    )
    departments = dept_result.scalars().all()

    department_stats: list[dict] = []
    for dept in departments:
        emp_ids_result = await db.execute(
            select(User.id).where(User.department_id == dept.id)
        )
        employee_ids = [row[0] for row in emp_ids_result.fetchall()]
        if not employee_ids:
            continue

        emp_count = len(employee_ids)

        high_stress_result = await db.execute(
            select(func.count(StressCheck.id))
            .where(
                and_(
                    StressCheck.user_id.in_(employee_ids),
                    StressCheck.period == period,
                    StressCheck.is_high_stress == True
                )
            )
        )
        high_stress_count = high_stress_result.scalar() or 0

        avg_result = await db.execute(
            select(func.avg(StressCheck.total_score))
            .where(
                and_(
                    StressCheck.user_id.in_(employee_ids),
                    StressCheck.period == period
                )
            )
        )
        avg_score = avg_result.scalar() or 0.0

        department_stats.append({
            "department_name": dept.name,
            "employee_count": emp_count,
            "high_stress_count": high_stress_count,
            "average_score": float(avg_score)
        })

    return department_stats


@router.get("/stress-check/{check_id}/pdf")
async def download_stress_check_pdf(
    check_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """個人のストレスチェック結果PDFをダウンロード"""
    # ストレスチェック結果を取得
    result = await db.execute(
        select(StressCheck).where(
            StressCheck.id == UUID(check_id),
            StressCheck.user_id == current_user.id
        )
    )
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ストレスチェック結果が見つかりません"
        )

    # スコアを計算
    scores = calculate_stress_scores(check.answers)

    # PDF生成
    pdf_generator = get_stress_check_pdf_generator()
    pdf_buffer = pdf_generator.generate_individual_report(
        user_name=current_user.email.split('@')[0],  # 簡易的にメールからユーザー名を取得
        period=check.period,
        total_score=check.total_score,
        is_high_stress=check.is_high_stress,
        job_stress_score=scores["job_stress_score"],
        stress_reaction_score=scores["stress_reaction_score"],
        support_score=scores["support_score"],
        satisfaction_score=scores["satisfaction_score"]
    )

    # ファイル名生成
    filename = f"stress_check_report_{check.period.strftime('%Y%m')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/company/{company_id}/group-analysis/pdf")
async def download_group_analysis_pdf(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """集団分析レポートPDFをダウンロード（管理者専用）"""
    # 管理者権限チェック
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    # 会社情報を取得
    company_result = await db.execute(
        select(Company).where(Company.id == UUID(company_id))
    )
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会社が見つかりません"
        )

    # 会社のユーザー一覧を取得
    users_result = await db.execute(
        select(User).where(User.company_id == UUID(company_id))
    )
    users = users_result.scalars().all()
    total_employees = len(users)

    if total_employees == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="従業員データがありません"
        )

    user_ids = [user.id for user in users]
    latest_period = await _get_latest_period(db, user_ids)
    if not latest_period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ストレスチェックのデータがありません"
        )

    # 高ストレス者数を取得
    high_stress_result = await db.execute(
        select(func.count(StressCheck.id))
        .where(
            and_(
                StressCheck.user_id.in_(user_ids),
                StressCheck.is_high_stress == True,
                StressCheck.period == latest_period
            )
        )
    )
    high_stress_count = high_stress_result.scalar() or 0

    # 受検者数を取得
    total_checks_result = await db.execute(
        select(func.count(func.distinct(StressCheck.user_id)))
        .where(
            and_(
                StressCheck.user_id.in_(user_ids),
                StressCheck.period == latest_period
            )
        )
    )
    total_checks = total_checks_result.scalar() or 0
    completion_rate = (total_checks / total_employees * 100) if total_employees > 0 else 0.0

    # 平均スコアを取得
    avg_score_result = await db.execute(
        select(func.avg(StressCheck.total_score))
        .where(
            and_(
                StressCheck.user_id.in_(user_ids),
                StressCheck.period == latest_period
            )
        )
    )
    average_stress_score = avg_score_result.scalar() or 0.0

    # 部署別統計（実データ）
    department_stats = await _get_department_stats_for_period(db, UUID(company_id), latest_period)

    # AI改善提案
    overall_stats = {
        "total_employees": total_employees,
        "high_stress_count": high_stress_count,
        "average_stress_score": float(average_stress_score),
        "stress_check_completion_rate": completion_rate
    }
    recommendations = await generate_improvement_recommendations(
        department_stats,
        overall_stats
    )

    # PDF生成
    pdf_generator = get_group_analysis_pdf_generator()
    pdf_buffer = pdf_generator.generate_company_report(
        company_name=company.name,
        period=latest_period,
        total_employees=total_employees,
        high_stress_count=high_stress_count,
        completion_rate=completion_rate,
        average_stress_score=float(average_stress_score),
        department_stats=department_stats,
        recommendations=recommendations
    )

    # ファイル名生成
    filename = f"group_analysis_report_{latest_period.strftime('%Y%m')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/company/{company_id}/department/{department_name}/pdf")
async def download_department_report_pdf(
    company_id: str,
    department_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """部署別統計レポートPDFをダウンロード（管理者専用）"""
    # 管理者権限チェック
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません"
        )

    # 会社情報を取得
    company_result = await db.execute(
        select(Company).where(Company.id == UUID(company_id))
    )
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会社が見つかりません"
        )

    # 部署を取得
    dept_result = await db.execute(
        select(Department).where(
            Department.company_id == UUID(company_id),
            Department.name == department_name
        )
    )
    department = dept_result.scalar_one_or_none()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署が見つかりません"
        )

    # 従業員一覧
    emp_ids_result = await db.execute(
        select(User.id).where(User.department_id == department.id)
    )
    employee_ids = [row[0] for row in emp_ids_result.fetchall()]
    employee_count = len(employee_ids)
    if employee_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部署の従業員データがありません"
        )

    latest_period = await _get_latest_period(db, employee_ids)
    if not latest_period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部署のストレスチェックデータがありません"
        )

    checks_result = await db.execute(
        select(StressCheck)
        .where(
            and_(
                StressCheck.user_id.in_(employee_ids),
                StressCheck.period == latest_period
            )
        )
    )
    checks = checks_result.scalars().all()
    if not checks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部署のストレスチェックデータがありません"
        )

    high_stress_count = sum(1 for c in checks if c.is_high_stress)
    average_score = sum(c.total_score for c in checks) / len(checks)

    # 詳細スコア平均
    job_stress_total = 0.0
    stress_reaction_total = 0.0
    support_total = 0.0
    satisfaction_total = 0.0
    for check in checks:
        scores = calculate_stress_scores(check.answers)
        job_stress_total += scores["job_stress_score"]
        stress_reaction_total += scores["stress_reaction_score"]
        support_total += scores["support_score"]
        satisfaction_total += scores["satisfaction_score"]

    count = len(checks)
    job_stress_avg = job_stress_total / count
    stress_reaction_avg = stress_reaction_total / count
    support_avg = support_total / count
    satisfaction_avg = satisfaction_total / count

    # PDF生成
    pdf_generator = get_department_report_pdf_generator()
    pdf_buffer = pdf_generator.generate_department_report(
        company_name=company.name,
        department_name=department.name,
        period=latest_period,
        employee_count=employee_count,
        high_stress_count=high_stress_count,
        average_score=average_score,
        job_stress_avg=job_stress_avg,
        stress_reaction_avg=stress_reaction_avg,
        support_avg=support_avg,
        satisfaction_avg=satisfaction_avg
    )

    # ファイル名生成
    filename = f"department_report_{department.name}_{latest_period.strftime('%Y%m')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
