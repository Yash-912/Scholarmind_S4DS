"""
Ops Routes — Full ops dashboard data: models, costs, drift, alerts, cache, scaling, prompts.
"""

from fastapi import APIRouter

from app.mlops.registry import model_registry
from app.mlops.drift_detector import drift_detector
from app.mlops.model_monitor import model_monitor
from app.mlops.quality_gate import quality_gate
from app.llmops.cost_tracker import cost_tracker
from app.llmops.cache import semantic_cache
from app.llmops.prompt_registry import prompt_registry
from app.aiops.health_monitor import health_monitor
from app.aiops.anomaly_detector import anomaly_detector
from app.aiops.auto_remediation import auto_remediation
from app.aiops.alerts import alert_engine
from app.aiops.scaling_advisor import scaling_advisor

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/models")
async def ops_models():
    """Get all registered models and their monitoring data."""
    return {
        "registry": await model_registry.list_models(),
        "monitoring": model_monitor.get_all_models(),
    }


@router.get("/costs")
async def ops_costs():
    """Get LLM cost data."""
    return cost_tracker.get_summary()


@router.get("/drift")
async def ops_drift():
    """Get drift detection history."""
    return await drift_detector.get_drift_history()


@router.get("/alerts")
async def ops_alerts():
    """Get all alerts."""
    # Evaluate rules first
    alert_engine.evaluate_all()
    return {
        "active": alert_engine.get_active_alerts(),
        "all": alert_engine.get_all_alerts(),
    }


@router.get("/anomalies")
async def ops_anomalies():
    """Get detected anomalies."""
    return {"anomalies": anomaly_detector.get_recent_anomalies()}


@router.get("/remediation")
async def ops_remediation():
    """Get auto-remediation actions and circuit breaker status."""
    return {
        "actions": auto_remediation.get_recent_actions(),
        "circuit_breakers": auto_remediation.get_circuit_breaker_status(),
    }


@router.get("/cache")
async def ops_cache():
    """Get semantic cache metrics."""
    return semantic_cache.get_stats()


@router.get("/scaling")
async def ops_scaling():
    """Get scaling recommendations and conference calendar."""
    metrics = await health_monitor.collect_metrics()
    system = metrics.get("system", {})
    return scaling_advisor.get_dashboard_data(
        cpu_percent=system.get("cpu_percent", 0),
        memory_percent=system.get("memory_percent", 0),
    )


@router.get("/prompts")
async def ops_prompts():
    """Get all prompt templates and usage stats."""
    return {"prompts": prompt_registry.list_templates()}


@router.get("/quality-gate")
async def ops_quality_gate():
    """Get quality gate baselines and status."""
    return {"baselines": quality_gate.BASELINES}
