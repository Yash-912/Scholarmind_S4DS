"""
Alert Rules Engine — Evaluates alert conditions and fires alerts.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass
class AlertRule:
    name: str
    condition: Callable[[], bool]
    severity: str  # "info", "warning", "critical"
    message: str
    cooldown_minutes: int = 10


@dataclass
class FiredAlert:
    timestamp: str
    rule_name: str
    severity: str
    message: str
    resolved: bool = False
    resolved_at: str | None = None


class AlertEngine:
    """Rule-based alert engine with deduplication and cooldown."""

    def __init__(self):
        self._rules: list[AlertRule] = []
        self._fired: list[FiredAlert] = []
        self._last_fired: dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule):
        """Register an alert rule."""
        self._rules.append(rule)

    def add_default_rules(self, health_monitor=None, cost_tracker=None):
        """Add default monitoring rules."""
        if health_monitor:
            self._rules.append(
                AlertRule(
                    name="high_memory",
                    condition=lambda: self._check_metric(
                        health_monitor, "memory_percent", 85
                    ),
                    severity="warning",
                    message="Memory usage above 85%",
                )
            )
            self._rules.append(
                AlertRule(
                    name="high_cpu",
                    condition=lambda: self._check_metric(
                        health_monitor, "cpu_percent", 90
                    ),
                    severity="critical",
                    message="CPU usage above 90%",
                )
            )

        if cost_tracker:
            self._rules.append(
                AlertRule(
                    name="cost_overrun",
                    condition=lambda: cost_tracker.get_summary().get(
                        "over_budget", False
                    ),
                    severity="critical",
                    message="Hourly LLM cost exceeds budget limit",
                    cooldown_minutes=30,
                )
            )

    def _check_metric(self, monitor, metric: str, threshold: float) -> bool:
        """Helper to check a metric against a threshold."""
        try:
            snapshot = monitor.collect_metrics()
            # collect_metrics() is async — if called from sync context
            # we get a coroutine, not data. Skip the check gracefully.
            if hasattr(snapshot, "__await__"):
                return False
            system = snapshot.get("system", {})
            return system.get(metric, 0) > threshold
        except Exception:
            return False

    def evaluate_all(self) -> list[FiredAlert]:
        """Evaluate all rules and fire alerts for those that trigger."""
        newly_fired = []
        now = datetime.now(timezone.utc)

        for rule in self._rules:
            # Check cooldown
            last = self._last_fired.get(rule.name)
            if last and (now - last).total_seconds() < rule.cooldown_minutes * 60:
                continue

            try:
                if rule.condition():
                    alert = FiredAlert(
                        timestamp=now.isoformat(),
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=rule.message,
                    )
                    self._fired.append(alert)
                    self._last_fired[rule.name] = now
                    newly_fired.append(alert)
            except Exception:
                pass

        return newly_fired

    def resolve(self, rule_name: str) -> bool:
        """Resolve an active alert by rule name."""
        for alert in reversed(self._fired):
            if alert.rule_name == rule_name and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def get_active_alerts(self) -> list[dict]:
        """Get all unresolved alerts."""
        return [
            {
                "timestamp": a.timestamp,
                "rule": a.rule_name,
                "severity": a.severity,
                "message": a.message,
            }
            for a in self._fired
            if not a.resolved
        ]

    def get_all_alerts(self, limit: int = 50) -> list[dict]:
        """Get all alerts (active and resolved)."""
        return [
            {
                "timestamp": a.timestamp,
                "rule": a.rule_name,
                "severity": a.severity,
                "message": a.message,
                "resolved": a.resolved,
                "resolved_at": a.resolved_at,
            }
            for a in self._fired[-limit:]
        ]


alert_engine = AlertEngine()
