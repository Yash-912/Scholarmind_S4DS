"""
Seed Papers — Fetch initial batch from arXiv and populate the database.
Can also be run as: python -m app.seed_papers (from backend dir)

Usage: python -m scripts.seed_papers
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed_papers import main

if __name__ == "__main__":
    asyncio.run(main())
