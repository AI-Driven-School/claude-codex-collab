"""
データベース接続設定
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://stressagent:password@localhost:5432/stressagent")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# 本番環境ではSQLログを無効化
engine = create_async_engine(DATABASE_URL, echo=DEBUG_MODE)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    データベースセッションを取得
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
