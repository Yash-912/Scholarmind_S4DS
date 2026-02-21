"""
Database connection and session management.
Supports both local SQLite (dev) and Neon PostgreSQL (production).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import os


# Determine which database to use
db_url = settings.db_url
is_postgres = "postgresql" in db_url or "postgres" in db_url

if not is_postgres:
    # Ensure data directory exists for SQLite
    db_path = db_url.replace("sqlite+aiosqlite:///", "")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

# Create async engine
engine_kwargs = {
    "echo": settings.DEBUG,
}

if not is_postgres:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings for production
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True  # Test connections before use
    # Neon requires SSL — asyncpg uses ssl=True in connect_args
    import ssl as _ssl

    ssl_ctx = _ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = _ssl.CERT_NONE
    engine_kwargs["connect_args"] = {"ssl": ssl_ctx}

engine = create_async_engine(db_url, **engine_kwargs)

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
    db_type = "PostgreSQL (Neon)" if is_postgres else "SQLite"
    print(f"✅ Database tables created ({db_type})")
