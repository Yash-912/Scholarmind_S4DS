"""
Scheduler — APScheduler for periodic ingestion jobs.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.ingestion.pipeline import run_ingestion_pipeline
from datetime import datetime, timezone


scheduler = AsyncIOScheduler()

# Track scheduler state
_scheduler_state = {
    "last_run": None,
    "next_run": None,
    "is_running": False,
    "last_result": None,
}


async def _scheduled_ingestion():
    """Scheduled ingestion job wrapper."""
    _scheduler_state["is_running"] = True
    _scheduler_state["last_run"] = datetime.now(timezone.utc).isoformat()

    try:
        result = await run_ingestion_pipeline()
        _scheduler_state["last_result"] = result
    except Exception as e:
        _scheduler_state["last_result"] = {"error": str(e)}
        print(f"❌ Scheduled ingestion failed: {e}")
    finally:
        _scheduler_state["is_running"] = False


def start_scheduler():
    """Start the periodic ingestion scheduler."""
    scheduler.add_job(
        _scheduled_ingestion,
        trigger=IntervalTrigger(hours=settings.SCRAPE_INTERVAL_HOURS),
        id="ingestion_pipeline",
        name="Paper Ingestion Pipeline",
        replace_existing=True,
    )
    scheduler.start()
    print(
        f"⏰ Scheduler started: ingestion every {settings.SCRAPE_INTERVAL_HOURS} hours"
    )


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("⏰ Scheduler stopped")


def get_scheduler_status() -> dict:
    """Get current scheduler state."""
    next_run = None
    job = scheduler.get_job("ingestion_pipeline")
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()

    return {
        **_scheduler_state,
        "next_run": next_run,
        "interval_hours": settings.SCRAPE_INTERVAL_HOURS,
        "scheduler_running": scheduler.running,
    }
