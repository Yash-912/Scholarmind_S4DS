"""Test Neon PostgreSQL and Upstash Redis connections."""
import asyncio
import sys
import os

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_neon():
    """Test Neon PostgreSQL connection."""
    print("=" * 50)
    print("Testing Neon PostgreSQL...")
    print("=" * 50)
    
    from app.config import settings
    db_url = settings.db_url
    print(f"  URL: {db_url[:50]}...")
    
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(db_url, pool_pre_ping=True)
    
    async with engine.connect() as conn:
        result = await conn.execute(__import__('sqlalchemy').text("SELECT version()"))
        version = result.scalar()
        print(f"  ✅ Connected! PostgreSQL version: {version[:60]}")
    
    await engine.dispose()
    print()

def test_redis():
    """Test Upstash Redis connection."""
    print("=" * 50)
    print("Testing Upstash Redis...")
    print("=" * 50)
    
    from app.config import settings
    redis_url = settings.REDIS_URL
    
    if not redis_url:
        print("  ⚠️ REDIS_URL not set, skipping")
        return
    
    print(f"  URL: {redis_url[:40]}...")
    
    import redis as r
    client = r.from_url(redis_url, decode_responses=True)
    
    # Test SET
    client.set("scholarmind:test", "hello_from_scholarmind")
    val = client.get("scholarmind:test")
    print(f"  ✅ SET/GET working: {val}")
    
    # Test PING
    pong = client.ping()
    print(f"  ✅ PING: {pong}")
    
    # Cleanup
    client.delete("scholarmind:test")
    client.close()
    print()

async def test_create_tables():
    """Test creating tables in Neon."""
    print("=" * 50)
    print("Creating tables in Neon PostgreSQL...")
    print("=" * 50)
    
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
