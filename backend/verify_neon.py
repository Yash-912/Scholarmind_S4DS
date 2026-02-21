"""Verify data in Neon PostgreSQL."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    from app.config import settings
    import ssl

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(settings.db_url, connect_args={"ssl": ssl_ctx})

    async with engine.connect() as conn:
        tables = [
            "papers",
            "model_versions",
            "query_logs",
            "ingestion_runs",
            "alerts",
            "topics",
        ]
        for table in tables:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count} rows")
            except Exception as e:
                print(f"  {table}: ERROR - {e}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
