"""
Pytest configuration and fixtures
"""

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.main import app
from app.database import get_db
from httpx import AsyncClient, ASGITransport


# postgresql.UUID has no SQLite rendering in the currently installed
# SQLAlchemy environment (GenericTypeCompiler has visit_uuid but not the
# visit_UUID this dialect-specific type dispatches to), which breaks
# Base.metadata.create_all against the in-memory SQLite test database
# below. Every model in this app uses postgresql.UUID directly since the
# real database is always Postgres - this shim is test-only and doesn't
# change anything about production behavior.
@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

pytest_plugins = ('pytest_asyncio',)


@pytest_asyncio.fixture
async def test_db():
    """Create test database and tables"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # SQLite doesn't enforce foreign key constraints unless explicitly told
    # to - without this, a broken FK reference (e.g. inserting a row with
    # a made-up UUID for a required foreign key) silently succeeds here but
    # would hard-fail against the real Postgres database, hiding real bugs.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
