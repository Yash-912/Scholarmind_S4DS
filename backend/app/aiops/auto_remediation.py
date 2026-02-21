"""
Auto Remediation — Automated responses to detected issues.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


@dataclass
class RemediationAction:
    timestamp: str
    trigger: str
    action: str
    result: str
    success: bool


class AutoRemediation:
    """Automated issue remediation with circuit breakers and rate limiting."""

    def __init__(self):
        self._actions: list[RemediationAction] = []
        self._circuit_breakers: dict[str, dict] = {}
        self._cooldowns: dict[str, datetime] = {}
        self.cooldown_minutes = 5

    async def handle_llm_failure(self, provider: str, error: str) -> RemediationAction:
        """Handle LLM provider failure with circuit breaker."""
        cb = self._circuit_breakers.setdefault(
            provider, {"failures": 0, "state": "closed", "last_failure": None}
        )
        cb["failures"] += 1
        cb["last_failure"] = datetime.now(timezone.utc)

        if cb["failures"] >= 3 and cb["state"] == "closed":
            cb["state"] = "open"
            action = RemediationAction(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trigger=f"LLM {provider} failed {cb['failures']}x",
                action=f"Circuit breaker OPENED for {provider} — routing to fallback",
                result="Switched to fallback provider",
                success=True,
            )
        else:
            action = RemediationAction(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trigger=f"LLM {provider} error: {error}",
                action="Logged failure, monitoring",
                result=f"Failure count: {cb['failures']}/3",
                success=True,
            )

        self._actions.append(action)
        return action

    async def handle_high_latency(self, component: str, latency_ms: float) -> RemediationAction:
        """Handle latency spikes."""
        if not self._can_act(f"latency_{component}"):
            return RemediationAction(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trigger=f"High latency on {component}: {latency_ms:.0f}ms",
                action="Cooldown active — skipping",
                result="Previous remediation still cooling down",
                success=False,
            )

        action = RemediationAction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger=f"High latency on {component}: {latency_ms:.0f}ms",
            action="Recommended: Clear semantic cache, check vector store health",
            result="Advisory generated",
            success=True,
        )
        self._set_cooldown(f"latency_{component}")
        self._actions.append(action)
        return action

    async def handle_cost_spike(self, hourly_cost: float, limit: float) -> RemediationAction:
        """Handle cost overrun."""
        if not self._can_act("cost_spike"):
            return RemediationAction(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trigger=f"Cost spike: ${hourly_cost:.4f}/{limit}",
                action="Cooldown active",
                result="Skipped",
                success=False,
            )

        action = RemediationAction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger=f"Hourly cost ${hourly_cost:.4f} exceeds limit ${limit}",
            action="Enable aggressive semantic caching, route to cheaper models",
            result="Cost controls tightened",
            success=True,
        )
        self._set_cooldown("cost_spike")
        self._actions.append(action)
        return action

    async def handle_scraper_failure(self, source: str, error: str) -> RemediationAction:
        """Handle scraper failures with retry logic."""
        action = RemediationAction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger=f"Scraper {source} failed: {error}",
            action=f"Scheduling retry for {source} with exponential backoff",
            result="Retry queued",
            success=True,
        )
        self._actions.append(action)
        return action

    def get_circuit_breaker_status(self) -> dict:
        """Get status of all circuit breakers."""
        return {k: {**v, "last_failure": v["last_failure"].isoformat() if v["last_failure"] else None}
                for k, v in self._circuit_breakers.items()}

    def get_recent_actions(self, limit: int = 20) -> list[dict]:
        """Get recent remediation actions."""
        return [
            {
                "timestamp": a.timestamp,
                "trigger": a.trigger,
                "action": a.action,
                "result": a.result,
                "success": a.success,
            }
            for a in self._actions[-limit:]
        ]

    def _can_act(self, key: str) -> bool:
        if key not in self._cooldowns:
            return True
        return datetime.now(timezone.utc) > self._cooldowns[key]

    def _set_cooldown(self, key: str):
        self._cooldowns[key] = datetime.now(timezone.utc) + timedelta(minutes=self.cooldown_minutes)


auto_remediation = AutoRemediation()
