"""
Feed Routes — Personalized paper recommendations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.db.models import User
from app.api.dependencies import get_current_user
from app.core.relevance import relevance_scorer

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get("")
async def get_feed(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized paper feed for the current user."""
    # Get user's bookmarked papers for profile
    bookmarks = await crud.get_user_bookmarks(db, user.id, limit=20)
    bookmarked_texts = [f"{p.title} {p.abstract[:200]}" for p in bookmarks]

    interests = user.interests or ["machine learning", "artificial intelligence"]

    feed = relevance_scorer.get_personalized_feed(
        interests=interests,
        bookmarked_texts=bookmarked_texts,
        top_k=20,
    )

    return {
        "user": user.username,
        "interests": interests,
        "feed": feed,
        "count": len(feed),
    }


@router.post("/interests")
async def update_interests(
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user interests."""
    interests = body.get("interests", [])
    user.interests = interests
    await db.flush()

    return {"message": "Interests updated", "interests": interests}


@router.post("/bookmark/{paper_id}")
async def add_bookmark(
    paper_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a paper."""
    paper = await crud.get_paper(db, paper_id)
    if not paper:
        return {"error": "Paper not found"}

    try:
        await crud.add_bookmark(db, user.id, paper_id)
        return {"message": "Bookmarked", "paper_id": paper_id}
    except Exception:
        return {"message": "Already bookmarked", "paper_id": paper_id}


@router.delete("/bookmark/{paper_id}")
async def remove_bookmark(
    paper_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a bookmark."""
    await crud.remove_bookmark(db, user.id, paper_id)
    return {"message": "Bookmark removed", "paper_id": paper_id}


@router.get("/bookmarks")
async def get_bookmarks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's bookmarked papers."""
    papers = await crud.get_user_bookmarks(db, user.id)
    return {
        "bookmarks": [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract[:200] + "...",
                "authors": p.authors,
                "source": p.source,
                "published_date": p.published_date.isoformat() if p.published_date else None,
            }
            for p in papers
        ],
        "count": len(papers),
    }
