"""
部署管理エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models import User, Department, UserRole
from app.models.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse
)
from app.routers.auth import get_current_user
from uuid import UUID

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


@router.get("", response_model=DepartmentListResponse)
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """会社の部署一覧を取得"""
    # 同じ会社の部署のみ取得
    result = await db.execute(
        select(Department).where(Department.company_id == current_user.company_id)
    )
    departments = result.scalars().all()

    # 各部署の従業員数を取得
    department_responses = []
    for dept in departments:
        emp_count_result = await db.execute(
            select(func.count(User.id)).where(User.department_id == dept.id)
        )
        employee_count = emp_count_result.scalar() or 0

        department_responses.append(DepartmentResponse(
            id=str(dept.id),
            name=dept.name,
            description=dept.description,
            company_id=str(dept.company_id),
            employee_count=employee_count,
            created_at=dept.created_at
        ))

    return DepartmentListResponse(
        departments=department_responses,
        total=len(department_responses)
    )


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """部署詳細を取得"""
    result = await db.execute(
        select(Department).where(
            Department.id == UUID(department_id),
            Department.company_id == current_user.company_id
        )
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署が見つかりません"
        )

    # 従業員数を取得
    emp_count_result = await db.execute(
        select(func.count(User.id)).where(User.department_id == department.id)
    )
    employee_count = emp_count_result.scalar() or 0

    return DepartmentResponse(
        id=str(department.id),
        name=department.name,
        description=department.description,
        company_id=str(department.company_id),
        employee_count=employee_count,
        created_at=department.created_at
    )


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """部署を作成（管理者のみ）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    # 同じ会社内で同名の部署がないか確認
    existing = await db.execute(
        select(Department).where(
            Department.company_id == current_user.company_id,
            Department.name == department_data.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同じ名前の部署が既に存在します"
        )

    new_department = Department(
        company_id=current_user.company_id,
        name=department_data.name,
        description=department_data.description
    )

    db.add(new_department)
    await db.commit()
    await db.refresh(new_department)

    return DepartmentResponse(
        id=str(new_department.id),
        name=new_department.name,
        description=new_department.description,
        company_id=str(new_department.company_id),
        employee_count=0,
        created_at=new_department.created_at
    )


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_data: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """部署を更新（管理者のみ）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    result = await db.execute(
        select(Department).where(
            Department.id == UUID(department_id),
            Department.company_id == current_user.company_id
        )
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署が見つかりません"
        )

    # 更新するフィールドのみ更新
    if department_data.name is not None:
        # 同じ名前の部署がないか確認
        existing = await db.execute(
            select(Department).where(
                Department.company_id == current_user.company_id,
                Department.name == department_data.name,
                Department.id != UUID(department_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="同じ名前の部署が既に存在します"
            )
        department.name = department_data.name

    if department_data.description is not None:
        department.description = department_data.description

    await db.commit()
    await db.refresh(department)

    # 従業員数を取得
    emp_count_result = await db.execute(
        select(func.count(User.id)).where(User.department_id == department.id)
    )
    employee_count = emp_count_result.scalar() or 0

    return DepartmentResponse(
        id=str(department.id),
        name=department.name,
        description=department.description,
        company_id=str(department.company_id),
        employee_count=employee_count,
        created_at=department.created_at
    )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """部署を削除（管理者のみ）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    result = await db.execute(
        select(Department).where(
            Department.id == UUID(department_id),
            Department.company_id == current_user.company_id
        )
    )
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署が見つかりません"
        )

    # 部署に所属するユーザーがいるか確認
    emp_count_result = await db.execute(
        select(func.count(User.id)).where(User.department_id == department.id)
    )
    employee_count = emp_count_result.scalar() or 0

    if employee_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"この部署には{employee_count}名の従業員が所属しています。先に従業員の部署を変更してください"
        )

    await db.delete(department)
    await db.commit()
