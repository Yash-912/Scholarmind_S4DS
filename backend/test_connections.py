"""Test Neon PostgreSQL and Upstash Redis connections."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_neon():
    print("=" * 50)
    print("Testing Neon PostgreSQL...")
    print("=" * 50)

    from app.config import settings

    db_url = settings.db_url
    print(f"  URL: {db_url[:60]}...")

    import ssl

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(db_url, connect_args={"ssl": ssl_ctx})

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"  ✅ Connected! {version[:70]}")

    await engine.dispose()
    print()


def test_redis():
    print("=" * 50)
    print("Testing Upstash Redis...")
    print("=" * 50)

    from app.config import settings

    redis_url = settings.REDIS_URL

    if not redis_url:
        print("  ⚠️ REDIS_URL not set, skipping")
        return

    print(f"  URL: {redis_url[:45]}...")

    import redis as r

    client = r.from_url(redis_url, decode_responses=True)

    client.set("scholarmind:test", "hello_from_scholarmind")
    val = client.get("scholarmind:test")
    print(f"  ✅ SET/GET working: {val}")

    pong = client.ping()
    print(f"  ✅ PING: {pong}")

    client.delete("scholarmind:test")
    client.close()
    print()


async def test_create_tables():
    print("=" * 50)
    print("Creating tables in Neon PostgreSQL...")
    print("=" * 50)

    # Import models so Base.metadata knows about them
    from app.db import models  # noqa
    from app.db.database import init_database

    await init_database()
    print()


async def main():
    await test_neon()
    test_redis()
    await test_create_tables()
    print("🎉 All connections verified!")


if __name__ == "__main__":
    asyncio.run(main())
