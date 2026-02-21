"""Drop all tables in Neon and recreate with timezone-aware columns."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from app.db.database import engine, Base
    from app.db import models  # noqa - register models

    print("Dropping all tables in Neon...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("OK - all tables dropped")

    print("Recreating tables with timezone=True columns...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("OK - all tables recreated")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
