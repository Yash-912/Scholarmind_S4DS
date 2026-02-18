"""
LLM Cost Tracker — Monitors LLM spending and triggers alerts.
"""

from datetime import datetime, timezone, timedelta
from collections import defaultdict
from app.config import settings


class CostTracker:
    """Tracks LLM API costs and provides spending analytics."""

    def __init__(self):
        self._costs: list[dict] = []
        self._hourly_limit = settings.LLM_COST_ALERT_PER_HOUR

    def record(self, model: str, provider: str, cost_usd: float, tokens: int):
        """Record a cost event."""
        self._costs.append({
            "model": model,
            "provider": provider,
            "cost_usd": cost_usd,
            "tokens": tokens,
            "timestamp": datetime.now(timezone.utc),
        })

    def get_hourly_spend(self) -> float:
        """Get total spend in the last hour."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        return sum(c["cost_usd"] for c in self._costs if c["timestamp"] > cutoff)

    def check_budget(self) -> dict:
        """Check if spending is within budget."""
        hourly = self.get_hourly_spend()
        over_budget = hourly > self._hourly_limit
        return {
            "hourly_spend_usd": round(hourly, 4),
            "hourly_limit_usd": self._hourly_limit,
            "over_budget": over_budget,
            "utilization_pct": round((hourly / max(self._hourly_limit, 0.001)) * 100, 1),
        }

    def get_breakdown(self, hours: int = 24) -> dict:
        """Get cost breakdown by model over the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = [c for c in self._costs if c["timestamp"] > cutoff]

        by_model = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "count": 0})
        for c in recent:
            by_model[c["model"]]["cost"] += c["cost_usd"]
            by_model[c["model"]]["tokens"] += c["tokens"]
            by_model[c["model"]]["count"] += 1

        return {
            "period_hours": hours,
            "total_cost_usd": round(sum(c["cost_usd"] for c in recent), 4),
            "total_tokens": sum(c["tokens"] for c in recent),
            "total_requests": len(recent),
            "by_model": {
                model: {
                    "cost_usd": round(data["cost"], 4),
                    "tokens": data["tokens"],
                    "requests": data["count"],
                }
                for model, data in by_model.items()
            },
        }

    def cleanup_old(self, max_hours: int = 48):
        """Remove cost records older than max_hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_hours)
        self._costs = [c for c in self._costs if c["timestamp"] > cutoff]


# Global singleton
cost_tracker = CostTracker()
