"""
データベース初期化スクリプト
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.database import Base, DATABASE_URL
from app.db.models import Company, User, Department, StressCheck, DailyScore, DraftAnswer

async def init_db():
    """テーブルを作成"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
