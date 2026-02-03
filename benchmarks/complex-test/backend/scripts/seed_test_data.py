"""
テスト用データのシードスクリプト
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.models import Company, User, UserRole, PlanType
from app.utils.security import get_password_hash
from uuid import UUID

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://stressagent:password@localhost:5432/stressagent")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_data():
    """テストデータをシード"""
    async with AsyncSessionLocal() as session:
        # テスト用企業を作成
        company = Company(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            name="テスト株式会社",
            industry="IT",
            plan_type=PlanType.BASIC
        )
        session.add(company)
        await session.flush()

        # 管理者ユーザーを作成
        admin_user = User(
            company_id=company.id,
            email="admin@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.ADMIN
        )
        session.add(admin_user)

        # 従業員ユーザーを作成
        employee_user = User(
            company_id=company.id,
            email="employee@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.EMPLOYEE
        )
        session.add(employee_user)

        await session.commit()
        print("テストデータのシードが完了しました")


if __name__ == "__main__":
    asyncio.run(seed_data())
