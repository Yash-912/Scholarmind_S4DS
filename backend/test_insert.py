"""Minimal test: insert one paper into Neon."""

import asyncio
import sys
import os
import traceback
import logging

logging.basicConfig(level=logging.DEBUG, filename="neon_debug.log", filemode="w")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    try:
        from app.db.database import init_database, async_session
        from app.db.models import Paper
        from datetime import datetime, timezone

        await init_database()
        print("Tables created")

        async with async_session() as db:
            paper = Paper(
                title="Test Paper",
                abstract="This is a test abstract.",
                authors=["Author A"],
                source="arxiv",
                source_id="test_neon_001",
                categories=["cs.AI"],
                references=[],
                published_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )
            db.add(paper)
            await db.commit()
            print(f"OK: id={paper.id}")

    except Exception as e:
        msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        print(msg[:3000])
        with open("neon_error.txt", "w") as f:
            f.write(msg)


if __name__ == "__main__":
    asyncio.run(main())
