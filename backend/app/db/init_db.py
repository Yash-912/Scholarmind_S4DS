"""
Database initialization — create tables and seed initial data.
"""

from app.db.database import init_database


async def initialize():
    """Create all database tables."""
    await init_database()
    print("✅ Database initialized successfully")
