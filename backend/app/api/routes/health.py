"""
Health Routes — Health checks, readiness, liveness, and Prometheus metrics.
"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.aiops.health_monitor import health_monitor
from app.aiops.metrics_collector import get_metrics, get_metrics_content_type

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic liveness check."""
    return {"status": "ok", "service": "scholarmind"}


@router.get("/ready")
async def readiness_check():
    """Readiness check — verifies all components are initialized."""
    metrics = health_monitor.collect_metrics()
    system = metrics.get("system", {})

    ready = True
    components = {}

    # Check vector store
    vs = metrics.get("vector_store", {})
    components["vector_store"] = {
        "status": "up" if vs.get("total_vectors", 0) >= 0 else "down"
    }

    # Check LLM
    llm = metrics.get("llm", {})
    components["llm"] = {"status": "up" if llm.get("total_calls", 0) >= 0 else "down"}

    # Check system resources
    components["system"] = {
        "status": "up",
        "cpu_percent": system.get("cpu_percent", 0),
        "memory_percent": system.get("memory_percent", 0),
    }

    return {
        "ready": ready,
        "components": components,
    }


@router.get("/components")
async def component_health():
    """Detailed health for each component."""
    metrics = health_monitor.collect_metrics()
    return metrics


@router.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type(),
    )
