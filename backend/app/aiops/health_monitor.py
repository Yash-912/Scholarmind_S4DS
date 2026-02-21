"""
AIOps — System health monitoring, anomaly detection, and auto-remediation.
"""

import os
import psutil
from datetime import datetime, timezone, timedelta
from collections import deque

from app.config import settings
from app.core.vector_store import vector_store
from app.llmops.gateway import llm_gateway
from app.llmops.cache import semantic_cache
from app.llmops.cost_tracker import cost_tracker
from app.db.database import async_session
from app.db import crud


class HealthMonitor:
    """
    AIOps health monitoring and anomaly detection.
    Tracks system metrics, detects anomalies, and triggers alerts.
    """

    def __init__(self):
        self._metrics_history: deque = deque(maxlen=1000)
        self._latency_history: deque = deque(maxlen=500)
        self._alert_cooldowns: dict[str, datetime] = {}

    async def collect_metrics(self) -> dict:
        """Collect all system health metrics."""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": self._get_system_metrics(),
            "vector_store": self._get_vector_store_metrics(),
            "llm": self._get_llm_metrics(),
            "cache": self._get_cache_metrics(),
            "cost": self._get_cost_metrics(),
        }

        self._metrics_history.append(metrics)
        return metrics

    def _get_system_metrics(self) -> dict:
        """Get system resource metrics."""
        try:
            process = psutil.Process(os.getpid())
            return {
                "cpu_percent": psutil.cpu_percent(interval=0),
                "memory_used_mb": round(process.memory_info().rss / 1024 / 1024, 1),
                "memory_percent": round(process.memory_percent(), 1),
                "disk_usage_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent,
            }
        except Exception:
            return {"cpu_percent": 0, "memory_used_mb": 0, "memory_percent": 0, "disk_usage_percent": 0}

    def _get_vector_store_metrics(self) -> dict:
        """Get vector store health metrics."""
        try:
            stats = vector_store.get_stats()
            return {
                "total_vectors": stats["total_vectors"],
                "status": "healthy" if stats["total_vectors"] >= 0 else "unhealthy",
            }
        except Exception:
            return {"total_vectors": 0, "status": "unreachable"}

    def _get_llm_metrics(self) -> dict:
        """Get LLM gateway metrics."""
        return llm_gateway.get_stats()

    def _get_cache_metrics(self) -> dict:
        """Get semantic cache metrics."""
        return semantic_cache.get_stats()

    def _get_cost_metrics(self) -> dict:
        """Get cost tracker metrics."""
        return cost_tracker.check_budget()

    async def check_anomalies(self, metrics: dict) -> list[dict]:
        """
        Check for anomalies in collected metrics and create alerts.

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check memory usage
        mem_pct = metrics.get("system", {}).get("memory_percent", 0)
        if mem_pct > 85:
            anomalies.append({
                "name": "high_memory",
                "severity": "warning",
                "message": f"Memory usage is at {mem_pct}%",
                "metric_name": "memory_percent",
                "metric_value": mem_pct,
                "threshold": 85,
                "remediation": "Consider restarting the service or reducing cache size",
            })

        # Check vector store
        vs_status = metrics.get("vector_store", {}).get("status", "")
        if vs_status == "unreachable":
            anomalies.append({
                "name": "vector_store_down",
                "severity": "critical",
                "message": "Vector store is unreachable",
                "metric_name": "vector_store_status",
                "metric_value": 0,
                "threshold": 1,
                "remediation": "Check ChromaDB process and disk space",
            })

        # Check cost budget
        cost_data = metrics.get("cost", {})
        if cost_data.get("over_budget"):
            anomalies.append({
                "name": "cost_overrun",
                "severity": "warning",
                "message": f"Hourly LLM spending (${cost_data.get('hourly_spend_usd', 0):.2f}) exceeds limit (${cost_data.get('hourly_limit_usd', 0):.2f})",
                "metric_name": "hourly_cost",
                "metric_value": cost_data.get("hourly_spend_usd", 0),
                "threshold": cost_data.get("hourly_limit_usd", 0),
                "remediation": "Route to smaller models or enable aggressive caching",
            })

        # Check cache health
        cache_data = metrics.get("cache", {})
        cache_hit_rate = cache_data.get("hit_rate", 0)
        total_cache = cache_data.get("hits", 0) + cache_data.get("misses", 0)
        if total_cache > 50 and cache_hit_rate < 0.1:
            anomalies.append({
                "name": "low_cache_hit_rate",
                "severity": "info",
                "message": f"Cache hit rate is only {cache_hit_rate*100:.1f}%",
                "metric_name": "cache_hit_rate",
                "metric_value": cache_hit_rate,
                "threshold": 0.1,
                "remediation": "Consider lowering the cache similarity threshold",
            })

        # Create alerts for anomalies (with cooldown)
        for anomaly in anomalies:
            await self._create_alert_if_new(anomaly)

        return anomalies

    async def _create_alert_if_new(self, anomaly: dict):
        """Create an alert only if it hasn't been raised recently."""
        name = anomaly["name"]
        cooldown = timedelta(minutes=settings.ALERT_COOLDOWN_MINUTES)

        if name in self._alert_cooldowns:
            last_alert = self._alert_cooldowns[name]
            if datetime.now(timezone.utc) - last_alert < cooldown:
                return  # Still in cooldown

        # Create alert
        async with async_session() as db:
            await crud.create_alert(
                db,
                name=anomaly["name"],
                severity=anomaly["severity"],
                message=anomaly["message"],
                metric_name=anomaly.get("metric_name"),
                metric_value=anomaly.get("metric_value"),
                threshold=anomaly.get("threshold"),
                remediation_action=anomaly.get("remediation"),
            )
            await db.commit()

        self._alert_cooldowns[name] = datetime.now(timezone.utc)
        print(f"🚨 ALERT [{anomaly['severity'].upper()}]: {anomaly['message']}")

    async def get_dashboard(self) -> dict:
        """Get full dashboard data."""
        metrics = await self.collect_metrics()
        anomalies = await self.check_anomalies(metrics)

        # Get recent alerts
        async with async_session() as db:
            alerts = await crud.get_recent_alerts(db, limit=10)
            query_stats = await crud.get_query_stats(db, hours=24)
            ingestion_stats = await crud.get_ingestion_stats(db, days=7)

        return {
            "metrics": metrics,
            "anomalies": anomalies,
            "alerts": [
                {
                    "id": a.id,
                    "name": a.name,
                    "severity": a.severity,
                    "message": a.message,
                    "resolved": a.resolved,
                    "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ],
            "query_stats": query_stats,
            "ingestion_stats": ingestion_stats,
        }

    def record_latency(self, endpoint: str, latency_ms: float):
        """Record API endpoint latency."""
        self._latency_history.append({
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc),
        })

    def get_latency_stats(self) -> dict:
        """Get latency statistics."""
        if not self._latency_history:
            return {"p50": 0, "p95": 0, "p99": 0, "count": 0}

        latencies = [entry["latency_ms"] for entry in self._latency_history]
        import numpy as np
        return {
            "p50": round(np.percentile(latencies, 50), 2),
            "p95": round(np.percentile(latencies, 95), 2),
            "p99": round(np.percentile(latencies, 99), 2),
            "count": len(latencies),
            "avg": round(np.mean(latencies), 2),
        }


# Global singleton
health_monitor = HealthMonitor()
