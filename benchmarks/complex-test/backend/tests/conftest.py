"""
テスト用共通フィクスチャ
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# テスト用環境変数を設定（モジュールインポート前に必要）
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-do-not-use-in-production"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DEBUG_MODE"] = "false"

from app.main import app
from app.db.database import Base, get_db


# テスト用データベース設定
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """イベントループをセッション全体で共有"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッション"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """テスト用HTTPクライアント"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict:
    """テスト用ユーザーデータ"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "company_name": "Test Company",
        "industry": "IT",
        "plan_type": "basic"
    }


@pytest.fixture
def test_login_data() -> dict:
    """テスト用ログインデータ"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
