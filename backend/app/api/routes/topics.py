"""
Topics Routes — Topic exploration, trending topics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.core.topic_model import topic_modeler

router = APIRouter(prefix="/topics", tags=["Topics"])


@router.get("")
async def list_topics(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all discovered topics."""
    topics = await crud.list_topics(db, limit)
    return {
        "topics": [
            {
                "id": t.id,
                "topic_id": t.topic_id,
                "name": t.name,
                "keywords": t.keywords,
                "paper_count": t.paper_count,
                "trend_direction": t.trend_direction,
            }
            for t in topics
        ],
        "count": len(topics),
    }


@router.get("/trending")
async def trending_topics(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get trending research topics."""
    topics = await crud.get_trending_topics(db, limit)
    return {
        "trending": [
            {
                "id": t.id,
                "name": t.name,
                "keywords": t.keywords,
                "paper_count": t.paper_count,
                "trend_direction": t.trend_direction,
            }
            for t in topics
        ],
    }


@router.get("/stats")
async def topic_stats():
    """Get topic model statistics."""
    return topic_modeler.get_stats()


@router.get("/{topic_id}/papers")
async def topic_papers(
    topic_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get papers in a specific topic."""
    papers = await crud.list_papers(db, topic_id=topic_id, limit=limit)
    return {
        "topic_id": topic_id,
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract[:200] + "...",
                "authors": p.authors,
                "published_date": p.published_date.isoformat()
                if p.published_date
                else None,
            }
            for p in papers
        ],
        "count": len(papers),
    }
