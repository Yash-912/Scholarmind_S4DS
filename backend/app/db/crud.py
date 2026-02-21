"""
Database CRUD operations for all models.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, Integer
from app.db.models import (
    Paper, Topic, User, Bookmark, QueryLog, Alert,
    ModelVersion, PromptUsage, IngestionRun, DriftRecord
)
from datetime import datetime, timezone, timedelta
from typing import Optional


# ═══════════════════════════════════════════
# PAPERS
# ═══════════════════════════════════════════

async def create_paper(db: AsyncSession, **kwargs) -> Paper:
    paper = Paper(**kwargs)
    db.add(paper)
    await db.flush()
    await db.refresh(paper)
    return paper


async def get_paper(db: AsyncSession, paper_id: int) -> Optional[Paper]:
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    return result.scalar_one_or_none()


async def get_paper_by_source_id(db: AsyncSession, source_id: str) -> Optional[Paper]:
    result = await db.execute(select(Paper).where(Paper.source_id == source_id))
    return result.scalar_one_or_none()


async def get_paper_by_doi(db: AsyncSession, doi: str) -> Optional[Paper]:
    if not doi:
        return None
    result = await db.execute(select(Paper).where(Paper.doi == doi))
    return result.scalar_one_or_none()


async def list_papers(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    topic_id: Optional[int] = None,
    sort_by: str = "published_date",
    order: str = "desc"
) -> list[Paper]:
    query = select(Paper)
    if source:
        query = query.where(Paper.source == source)
    if topic_id:
        query = query.where(Paper.topic_id == topic_id)

    order_col = getattr(Paper, sort_by, Paper.published_date)
    if order == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(order_col)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_papers(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Paper.id)))
    return result.scalar() or 0


async def search_papers_by_title(db: AsyncSession, query: str, limit: int = 20) -> list[Paper]:
    result = await db.execute(
        select(Paper)
        .where(Paper.title.ilike(f"%{query}%"))
        .order_by(desc(Paper.published_date))
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_paper_topic(db: AsyncSession, paper_id: int, topic_id: int):
    paper = await get_paper(db, paper_id)
    if paper:
        paper.topic_id = topic_id
        await db.flush()


async def update_paper_novelty(db: AsyncSession, paper_id: int, score: float, novelty_type: str):
    paper = await get_paper(db, paper_id)
    if paper:
        paper.novelty_score = score
        paper.novelty_type = novelty_type
        await db.flush()


# ═══════════════════════════════════════════
# TOPICS
# ═══════════════════════════════════════════

async def create_topic(db: AsyncSession, **kwargs) -> Topic:
    topic = Topic(**kwargs)
    db.add(topic)
    await db.flush()
    await db.refresh(topic)
    return topic


async def get_topic(db: AsyncSession, topic_id: int) -> Optional[Topic]:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    return result.scalar_one_or_none()


async def get_topic_by_topic_id(db: AsyncSession, topic_id: int) -> Optional[Topic]:
    result = await db.execute(select(Topic).where(Topic.topic_id == topic_id))
    return result.scalar_one_or_none()


async def list_topics(db: AsyncSession, limit: int = 50) -> list[Topic]:
    result = await db.execute(
        select(Topic).order_by(desc(Topic.paper_count)).limit(limit)
    )
    return list(result.scalars().all())


async def get_trending_topics(db: AsyncSession, limit: int = 10) -> list[Topic]:
    result = await db.execute(
        select(Topic)
        .where(Topic.trend_direction == "rising")
        .order_by(desc(Topic.paper_count))
        .limit(limit)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════
# USERS & BOOKMARKS
# ═══════════════════════════════════════════

async def get_or_create_user(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        user = User(username=username)
        db.add(user)
        await db.flush()
        await db.refresh(user)
    return user


async def add_bookmark(db: AsyncSession, user_id: int, paper_id: int) -> Bookmark:
    bookmark = Bookmark(user_id=user_id, paper_id=paper_id)
    db.add(bookmark)
    await db.flush()
    return bookmark


async def remove_bookmark(db: AsyncSession, user_id: int, paper_id: int):
    result = await db.execute(
        select(Bookmark).where(
            and_(Bookmark.user_id == user_id, Bookmark.paper_id == paper_id)
        )
    )
    bookmark = result.scalar_one_or_none()
    if bookmark:
        await db.delete(bookmark)
        await db.flush()


async def get_user_bookmarks(db: AsyncSession, user_id: int, limit: int = 50) -> list[Paper]:
    result = await db.execute(
        select(Paper)
        .join(Bookmark, Bookmark.paper_id == Paper.id)
        .where(Bookmark.user_id == user_id)
        .order_by(desc(Bookmark.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════
# QUERY LOGS
# ═══════════════════════════════════════════

async def log_query(db: AsyncSession, **kwargs) -> QueryLog:
    log = QueryLog(**kwargs)
    db.add(log)
    await db.flush()
    return log


async def get_query_stats(db: AsyncSession, hours: int = 24) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(
            func.count(QueryLog.id).label("total_queries"),
            func.avg(QueryLog.latency_ms).label("avg_latency"),
            func.sum(QueryLog.cost_usd).label("total_cost"),
            func.avg(QueryLog.faithfulness_score).label("avg_faithfulness"),
            func.sum(func.cast(QueryLog.cache_hit, Integer)).label("cache_hits"),
        ).where(QueryLog.timestamp >= since)
    )
    row = result.one()
    total = row.total_queries or 0
    return {
        "total_queries": total,
        "avg_latency_ms": round(row.avg_latency or 0, 2),
        "total_cost_usd": round(row.total_cost or 0, 4),
        "avg_faithfulness": round(row.avg_faithfulness or 0, 3),
        "cache_hit_rate": round((row.cache_hits or 0) / max(total, 1), 3),
        "period_hours": hours,
    }


async def get_recent_queries(db: AsyncSession, limit: int = 20) -> list[QueryLog]:
    result = await db.execute(
        select(QueryLog).order_by(desc(QueryLog.timestamp)).limit(limit)
    )
    return list(result.scalars().all())


async def get_cost_by_model(db: AsyncSession, hours: int = 24) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(
            QueryLog.model_used,
            func.count(QueryLog.id).label("count"),
            func.sum(QueryLog.cost_usd).label("total_cost"),
            func.sum(QueryLog.input_tokens).label("total_input_tokens"),
            func.sum(QueryLog.output_tokens).label("total_output_tokens"),
        )
        .where(QueryLog.timestamp >= since)
        .group_by(QueryLog.model_used)
    )
    return [
        {
            "model": row.model_used,
            "count": row.count,
            "total_cost": round(row.total_cost or 0, 4),
            "total_input_tokens": row.total_input_tokens or 0,
            "total_output_tokens": row.total_output_tokens or 0,
        }
        for row in result.all()
    ]


# ═══════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════

async def create_alert(db: AsyncSession, **kwargs) -> Alert:
    alert = Alert(**kwargs)
    db.add(alert)
    await db.flush()
    return alert


async def get_recent_alerts(db: AsyncSession, limit: int = 20, include_resolved: bool = False) -> list[Alert]:
    query = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    if not include_resolved:
        query = query.where(Alert.resolved.is_(False))
    result = await db.execute(query)
    return list(result.scalars().all())


async def resolve_alert(db: AsyncSession, alert_id: int):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert:
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        await db.flush()


# ═══════════════════════════════════════════
# MODEL VERSIONS
# ═══════════════════════════════════════════

async def register_model_version(db: AsyncSession, **kwargs) -> ModelVersion:
    mv = ModelVersion(**kwargs)
    db.add(mv)
    await db.flush()
    return mv


async def list_model_versions(db: AsyncSession) -> list[ModelVersion]:
    result = await db.execute(
        select(ModelVersion).order_by(desc(ModelVersion.registered_at))
    )
    return list(result.scalars().all())


async def get_active_model(db: AsyncSession, name: str) -> Optional[ModelVersion]:
    result = await db.execute(
        select(ModelVersion)
        .where(and_(ModelVersion.name == name, ModelVersion.is_active.is_(True)))
        .order_by(desc(ModelVersion.registered_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


# ═══════════════════════════════════════════
# INGESTION RUNS
# ═══════════════════════════════════════════

async def create_ingestion_run(db: AsyncSession, **kwargs) -> IngestionRun:
    run = IngestionRun(**kwargs)
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def complete_ingestion_run(db: AsyncSession, run_id: int, **kwargs):
    result = await db.execute(select(IngestionRun).where(IngestionRun.id == run_id))
    run = result.scalar_one_or_none()
    if run:
        for k, v in kwargs.items():
            setattr(run, k, v)
        run.completed_at = datetime.now(timezone.utc)
        await db.flush()


async def get_latest_ingestion_run(db: AsyncSession) -> Optional[IngestionRun]:
    result = await db.execute(
        select(IngestionRun).order_by(desc(IngestionRun.started_at)).limit(1)
    )
    return result.scalar_one_or_none()


async def get_ingestion_stats(db: AsyncSession, days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(IngestionRun.id).label("total_runs"),
            func.sum(IngestionRun.papers_new).label("total_new"),
            func.sum(IngestionRun.papers_duplicate).label("total_duplicates"),
            func.avg(IngestionRun.duration_seconds).label("avg_duration"),
        ).where(IngestionRun.started_at >= since)
    )
    row = result.one()
    return {
        "total_runs": row.total_runs or 0,
        "total_new_papers": row.total_new or 0,
        "total_duplicates": row.total_duplicates or 0,
        "avg_duration_seconds": round(row.avg_duration or 0, 2),
    }


# ═══════════════════════════════════════════
# DRIFT RECORDS
# ═══════════════════════════════════════════

async def create_drift_record(db: AsyncSession, **kwargs) -> DriftRecord:
    record = DriftRecord(**kwargs)
    db.add(record)
    await db.flush()
    return record


async def get_recent_drift_records(db: AsyncSession, limit: int = 20) -> list[DriftRecord]:
    result = await db.execute(
        select(DriftRecord).order_by(desc(DriftRecord.detected_at)).limit(limit)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════
# PROMPT USAGE
# ═══════════════════════════════════════════

async def log_prompt_usage(db: AsyncSession, **kwargs) -> PromptUsage:
    usage = PromptUsage(**kwargs)
    db.add(usage)
    await db.flush()
    return usage


async def get_prompt_stats(db: AsyncSession, prompt_name: str) -> dict:
    result = await db.execute(
        select(
            PromptUsage.prompt_version,
            func.count(PromptUsage.id).label("usage_count"),
            func.avg(PromptUsage.faithfulness).label("avg_faithfulness"),
            func.avg(PromptUsage.relevance).label("avg_relevance"),
            func.avg(PromptUsage.tokens_used).label("avg_tokens"),
        )
        .where(PromptUsage.prompt_name == prompt_name)
        .group_by(PromptUsage.prompt_version)
    )
    return [
        {
            "version": row.prompt_version,
            "usage_count": row.usage_count,
            "avg_faithfulness": round(row.avg_faithfulness or 0, 3),
            "avg_relevance": round(row.avg_relevance or 0, 3),
            "avg_tokens": round(row.avg_tokens or 0),
        }
        for row in result.all()
    ]
