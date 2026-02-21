"""
Model Monitor — Continuous monitoring of deployed model performance.
Tracks throughput, latency, and quality signals over time.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ModelMetricSnapshot:
    timestamp: str
    model_name: str
    metric_name: str
    value: float


class ModelMonitor:
    """Tracks model performance metrics over time and triggers alerts on degradation."""

    def __init__(self, window_size: int = 500):
        self.window_size = window_size
        # {model_name: {metric_name: deque of (timestamp, value)}}
        self._metrics: dict[str, dict[str, deque]] = {}

    def record(self, model_name: str, metric_name: str, value: float):
        """Record a metric observation."""
        if model_name not in self._metrics:
            self._metrics[model_name] = {}
        if metric_name not in self._metrics[model_name]:
            self._metrics[model_name][metric_name] = deque(maxlen=self.window_size)

        self._metrics[model_name][metric_name].append(
            (datetime.now(timezone.utc).isoformat(), value)
        )

    def get_stats(self, model_name: str, metric_name: str) -> dict:
        """Get statistics for a specific model metric."""
        values = self._get_values(model_name, metric_name)
        if not values:
            return {"count": 0}

        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
            "p50": sorted(values)[len(values) // 2],
            "p95": sorted(values)[int(len(values) * 0.95)]
            if len(values) >= 20
            else None,
        }

    def check_degradation(
        self, model_name: str, metric_name: str, threshold_pct: float = 10.0
    ) -> dict:
        """Check if a metric is degrading by comparing recent vs historical performance."""
        values = self._get_values(model_name, metric_name)
        if len(values) < 20:
            return {"degraded": False, "reason": "Insufficient data"}

        mid = len(values) // 2
        historical_avg = sum(values[:mid]) / mid
        recent_avg = sum(values[mid:]) / (len(values) - mid)

        if historical_avg == 0:
            return {"degraded": False, "reason": "Historical avg is zero"}

        change_pct = ((recent_avg - historical_avg) / abs(historical_avg)) * 100

        # For latency metrics, positive change is bad; for quality metrics negative is bad
        is_latency = "latency" in metric_name or "time" in metric_name
        degraded = (
            change_pct > threshold_pct if is_latency else change_pct < -threshold_pct
        )

        return {
            "degraded": degraded,
            "historical_avg": historical_avg,
            "recent_avg": recent_avg,
            "change_pct": change_pct,
            "direction": "increased" if change_pct > 0 else "decreased",
        }

    def get_all_models(self) -> dict:
        """Get summary of all monitored models."""
        summary = {}
        for model_name, metrics in self._metrics.items():
            summary[model_name] = {
                metric_name: self.get_stats(model_name, metric_name)
                for metric_name in metrics
            }
        return summary

    def _get_values(self, model_name: str, metric_name: str) -> list[float]:
        if model_name not in self._metrics:
            return []
        if metric_name not in self._metrics[model_name]:
            return []
        return [v for _, v in self._metrics[model_name][metric_name]]


model_monitor = ModelMonitor()
