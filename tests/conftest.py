"""
Test Configuration

pytest 설정 및 공통 fixtures
"""

import pytest
import pytest_asyncio
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# 테스트 환경 변수 설정
os.environ.update({
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "REDIS_URL": "redis://localhost:6379/1",
    "GITHUB_TOKEN": "test_token",
    "SECRET_KEY": "test_secret_key"
})

from app.core.database import Base
from app.core.config import Settings


# 테스트용 설정
class TestSettings(Settings):
    """테스트 환경 설정"""
    database_url: str = "sqlite+aiosqlite:///:memory:"
    redis_url: str = "redis://localhost:6379/1"  # 테스트용 DB
    debug: bool = True
    
    class Config:
        env_file = None


@pytest.fixture(scope="session")
def event_loop():
    """비동기 테스트를 위한 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """테스트용 데이터베이스 엔진"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 정리
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """테스트용 데이터베이스 세션"""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            yield session
            await session.rollback()  # 테스트 후 롤백
        finally:
            await session.close()


@pytest.fixture
def test_settings():
    """테스트용 설정"""
    return TestSettings()