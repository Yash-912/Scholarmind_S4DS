"""
Shared test fixtures — provides a test-safe database and FastAPI client.

Overrides the production DB (Neon Postgres) with an in-process SQLite DB
so that tests never touch the real database and avoid asyncpg event-loop
mismatches with Starlette's synchronous TestClient.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.api.dependencies import get_current_user
from app.main import app

# ── Test database: in-memory SQLite (fast, isolated, no loop issues) ──
TEST_DB_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # single connection shared across threads
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Dependency overrides ──
async def override_get_db():
    """Yield a session bound to the test SQLite database."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class _FakeUser:
    """Minimal user object for tests (avoids DB lookup)."""

    id = 1
    username = "test-user"
    interests = ["machine learning"]
    created_at = "2025-01-01T00:00:00Z"


async def override_get_current_user():
    return _FakeUser()


# ── Apply overrides ──
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# ── Fixtures ──
@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all ORM tables in the test DB once per test session."""
    import asyncio

    async def _create():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield
    # tables disappear when the in-memory engine is GC'd


@pytest.fixture(scope="session")
def client():
    """Reusable TestClient scoped to the full test session."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
