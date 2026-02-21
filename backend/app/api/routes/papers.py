"""
Paper Routes — Search, list, and get paper details.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db import crud
from app.core.novelty import novelty_detector

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.get("")
async def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source: str = Query(None),
    topic_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List papers with pagination and optional filtering."""
    papers = await crud.list_papers(
        db, skip=skip, limit=limit, source=source, topic_id=topic_id
    )
    total = await crud.count_papers(db)
    return {
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract[:300] + "..."
                if len(p.abstract) > 300
                else p.abstract,
                "authors": p.authors,
                "source": p.source,
                "source_id": p.source_id,
                "published_date": p.published_date.isoformat()
                if p.published_date
                else None,
                "categories": p.categories,
                "citation_count": p.citation_count,
                "novelty_score": p.novelty_score,
                "topic_id": p.topic_id,
            }
            for p in papers
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search papers by title."""
    papers = await crud.search_papers_by_title(db, q, limit)
    return {
        "query": q,
        "results": [
            {
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract[:200] + "...",
                "authors": p.authors,
                "source": p.source,
                "published_date": p.published_date.isoformat()
                if p.published_date
                else None,
                "novelty_score": p.novelty_score,
            }
            for p in papers
        ],
        "count": len(papers),
    }


@router.get("/count")
async def paper_count(db: AsyncSession = Depends(get_db)):
    """Get total paper count."""
    total = await crud.count_papers(db)
    return {"total": total}


@router.get("/{paper_id}")
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single paper by ID."""
    paper = await crud.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {
        "id": paper.id,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors,
        "source": paper.source,
        "source_id": paper.source_id,
        "doi": paper.doi,
        "published_date": paper.published_date.isoformat()
        if paper.published_date
        else None,
        "categories": paper.categories,
        "references": paper.references,
        "citation_count": paper.citation_count,
        "pdf_url": paper.pdf_url,
        "novelty_score": paper.novelty_score,
        "novelty_type": paper.novelty_type,
        "topic_id": paper.topic_id,
        "created_at": paper.created_at.isoformat(),
    }


@router.get("/{paper_id}/novelty")
async def get_paper_novelty(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get novelty analysis for a paper."""
    paper = await crud.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    result = novelty_detector.score_novelty(
        title=paper.title,
        abstract=paper.abstract,
        categories=paper.categories,
    )

    # Update in DB
    await crud.update_paper_novelty(
        db, paper_id, result["novelty_score"], result["novelty_type"]
    )

    return {
        "paper_id": paper_id,
        "title": paper.title,
        **result,
    }
