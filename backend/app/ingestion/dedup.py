"""
Deduplication — Detect duplicate papers across sources.
Uses DOI exact match and title fuzzy matching.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from rapidfuzz import fuzz
from app.db import crud


TITLE_SIMILARITY_THRESHOLD = 90  # 90% match = duplicate


async def is_duplicate(
    db: AsyncSession,
    source_id: str,
    doi: str | None = None,
    title: str | None = None,
) -> tuple[bool, int | None]:
    """
    Check if a paper is a duplicate.

    Returns:
        (is_duplicate: bool, existing_paper_id: int | None)
    """
    # Check 1: Exact source_id match
    existing = await crud.get_paper_by_source_id(db, source_id)
    if existing:
        return True, existing.id

    # Check 2: DOI match
    if doi:
        existing = await crud.get_paper_by_doi(db, doi)
        if existing:
            return True, existing.id

    # Check 3: Title fuzzy match (only if title is reasonably long)
    if title and len(title) > 20:
        # Search for papers with similar titles
        candidates = await crud.search_papers_by_title(db, title[:50], limit=10)
        for candidate in candidates:
            similarity = fuzz.ratio(title.lower(), candidate.title.lower())
            if similarity >= TITLE_SIMILARITY_THRESHOLD:
                return True, candidate.id

    return False, None
