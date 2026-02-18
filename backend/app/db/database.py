"""
Database connection and session management.
Uses async SQLite via aiosqlite + SQLAlchemy async.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import os


# Ensure data directory exists
os.makedirs(os.path.dirname(settings.SQLITE_URL.replace("sqlite+aiosqlite:///", "")), exist_ok=True)

# Create async engine
engine = create_async_engine(
    settings.SQLITE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")
