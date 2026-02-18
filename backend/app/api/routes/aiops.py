"""
AIOps Routes — Health monitoring, alerts, dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.aiops.health_monitor import health_monitor

router = APIRouter(prefix="/aiops", tags=["AIOps"])


@router.get("/dashboard")
async def dashboard():
    """Get full AIOps dashboard data."""
    return await health_monitor.get_dashboard()


@router.get("/health")
async def health_check():
    """Quick health check endpoint."""
    metrics = await health_monitor.collect_metrics()
    return {
        "status": "healthy",
        "timestamp": metrics["timestamp"],
        "system": metrics["system"],
        "vector_store": metrics["vector_store"],
    }


@router.get("/metrics")
async def current_metrics():
    """Get current system metrics."""
    return await health_monitor.collect_metrics()


@router.get("/alerts")
async def list_alerts(
    limit: int = 20,
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get recent alerts."""
    alerts = await crud.get_recent_alerts(db, limit, include_resolved)
    return {
        "alerts": [
            {
                "id": a.id,
                "name": a.name,
                "severity": a.severity,
                "message": a.message,
                "metric_name": a.metric_name,
                "metric_value": a.metric_value,
                "threshold": a.threshold,
                "resolved": a.resolved,
                "remediation_action": a.remediation_action,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Resolve an alert."""
    await crud.resolve_alert(db, alert_id)
    return {"message": f"Alert {alert_id} resolved"}


@router.get("/latency")
async def latency_stats():
    """Get API latency statistics."""
    return health_monitor.get_latency_stats()
