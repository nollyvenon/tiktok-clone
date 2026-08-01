"""
Pytest configuration and fixtures
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.main import app
from app.database import get_db
from httpx import AsyncClient, ASGITransport


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

pytest_plugins = ('pytest_asyncio',)


@pytest_asyncio.fixture
async def test_db():
    """Create test database and tables"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_client(test_db):
    """Create test HTTP client with test database"""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def register_user_data():
    """Sample user registration data"""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "Test@1234Password",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def login_user_data():
    """Sample user login data"""
    return {
        "email": "testuser@example.com",
        "password": "Test@1234Password",
    }
