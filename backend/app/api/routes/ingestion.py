"""
Ingestion Routes — Trigger and monitor data ingestion pipelines.
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.ingestion.pipeline import run_ingestion_pipeline
from app.ingestion.scheduler import get_scheduler_status

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/run")
async def trigger_ingestion(
    body: dict = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Trigger an ingestion pipeline run.

    Body:
        sources: Optional list of sources (default: ["arxiv", "pubmed"])
        max_arxiv: Optional max arXiv results
        max_pubmed: Optional max PubMed results
        background: Whether to run in background (default: true)
    """
    body = body or {}
    sources = body.get("sources", ["arxiv", "pubmed"])
    max_arxiv = body.get("max_arxiv")
    max_pubmed = body.get("max_pubmed")
    run_bg = body.get("background", True)

    if run_bg and background_tasks:
        background_tasks.add_task(
            run_ingestion_pipeline,
            sources=sources,
            max_arxiv=max_arxiv,
            max_pubmed=max_pubmed,
        )
        return {
            "message": "Ingestion pipeline started in background",
            "sources": sources,
        }

    result = await run_ingestion_pipeline(
        sources=sources,
        max_arxiv=max_arxiv,
        max_pubmed=max_pubmed,
    )
    return result


@router.get("/status")
async def ingestion_status(db: AsyncSession = Depends(get_db)):
    """Get latest ingestion run status and scheduler info."""
    latest = await crud.get_latest_ingestion_run(db)
    scheduler = get_scheduler_status()

    return {
        "latest_run": {
            "id": latest.id,
            "source": latest.source,
            "status": latest.status,
            "papers_found": latest.papers_found,
            "papers_new": latest.papers_new,
            "papers_duplicate": latest.papers_duplicate,
            "duration_seconds": latest.duration_seconds,
            "started_at": latest.started_at.isoformat(),
            "completed_at": latest.completed_at.isoformat()
            if latest.completed_at
            else None,
        }
        if latest
        else None,
        "scheduler": scheduler,
    }


@router.get("/stats")
async def ingestion_stats(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Get ingestion statistics over the last N days."""
    stats = await crud.get_ingestion_stats(db, days)
    return stats
