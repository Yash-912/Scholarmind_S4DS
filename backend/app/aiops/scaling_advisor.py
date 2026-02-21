"""
Scaling Advisor — Load analysis and conference calendar-based scaling recommendations.
"""

from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class ScalingAdvice:
    timestamp: str
    category: str  # "conference_surge", "load_pattern", "resource"
    severity: str  # "info", "warning", "action_required"
    title: str
    description: str
    recommendation: str


# Major ML/AI conference dates (approximate submission-to-publication cycles)
CONFERENCE_CALENDAR = [
    {"name": "NeurIPS", "month": 12, "surge_start_month": 9, "field": "ML"},
    {"name": "ICML", "month": 7, "surge_start_month": 4, "field": "ML"},
    {"name": "ICLR", "month": 5, "surge_start_month": 1, "field": "ML"},
    {"name": "ACL", "month": 7, "surge_start_month": 4, "field": "NLP"},
    {"name": "EMNLP", "month": 12, "surge_start_month": 8, "field": "NLP"},
    {"name": "CVPR", "month": 6, "surge_start_month": 3, "field": "CV"},
    {"name": "ICCV", "month": 10, "surge_start_month": 7, "field": "CV"},
    {"name": "ECCV", "month": 10, "surge_start_month": 6, "field": "CV"},
    {"name": "AAAI", "month": 2, "surge_start_month": 11, "field": "AI"},
    {"name": "IJCAI", "month": 8, "surge_start_month": 5, "field": "AI"},
    {"name": "KDD", "month": 8, "surge_start_month": 5, "field": "Data Mining"},
    {"name": "WWW", "month": 5, "surge_start_month": 2, "field": "Web"},
]


class ScalingAdvisor:
    """Provides scaling recommendations based on load patterns and conference schedules."""

    def get_upcoming_conferences(self, lookahead_days: int = 90) -> list[dict]:
        """Get conferences with paper surges expected in the next N days."""
        now = datetime.now(timezone.utc)
        upcoming = []

        for conf in CONFERENCE_CALENDAR:
            # Check if the surge start date falls within our lookahead window
            for year_offset in [0, 1]:
                surge_month = conf["surge_start_month"]
                conf_month = conf["month"]
                year = now.year + year_offset

                surge_date = datetime(year, surge_month, 1, tzinfo=timezone.utc)
                conf_date = datetime(
                    year if conf_month >= surge_month else year + 1,
                    conf_month,
                    1,
                    tzinfo=timezone.utc,
                )

                days_until = (surge_date - now).days
                if 0 <= days_until <= lookahead_days:
                    upcoming.append(
                        {
                            "name": conf["name"],
                            "field": conf["field"],
                            "conference_date": conf_date.strftime("%B %Y"),
                            "surge_starts": surge_date.strftime("%B %Y"),
                            "days_until_surge": days_until,
                        }
                    )

        return sorted(upcoming, key=lambda x: x["days_until_surge"])

    def get_scaling_advice(
        self,
        current_papers: int = 0,
        daily_queries: int = 0,
        cpu_percent: float = 0,
        memory_percent: float = 0,
    ) -> list[ScalingAdvice]:
        """Generate scaling recommendations."""
        advice = []
        now = datetime.now(timezone.utc).isoformat()

        # Conference-based advisories
        upcoming = self.get_upcoming_conferences(lookahead_days=60)
        for conf in upcoming[:3]:
            advice.append(
                ScalingAdvice(
                    timestamp=now,
                    category="conference_surge",
                    severity="info" if conf["days_until_surge"] > 30 else "warning",
                    title=f"{conf['name']} paper surge approaching",
                    description=(
                        f"{conf['name']} ({conf['field']}) papers expected to surge "
                        f"in {conf['days_until_surge']} days. Conference in {conf['conference_date']}."
                    ),
                    recommendation=(
                        f"Increase {conf['field']}-related category scraping. "
                        "Consider pre-warming the embedding cache with related search terms."
                    ),
                )
            )

        # Resource-based advisories
        if cpu_percent > 80:
            advice.append(
                ScalingAdvice(
                    timestamp=now,
                    category="resource",
                    severity="action_required",
                    title="High CPU usage",
                    description=f"CPU at {cpu_percent:.0f}%. Embedding and topic modeling may be contending.",
                    recommendation="Reduce concurrent embedding batch size. Consider disabling re-ranker for low-priority queries.",
                )
            )

        if memory_percent > 80:
            advice.append(
                ScalingAdvice(
                    timestamp=now,
                    category="resource",
                    severity="warning" if memory_percent < 90 else "action_required",
                    title="High memory usage",
                    description=f"Memory at {memory_percent:.0f}%. ChromaDB and BM25 index are memory-intensive.",
                    recommendation="Reduce BM25 index size, increase semantic cache eviction, or reduce ChromaDB segment count.",
                )
            )

        # Load pattern advisories
        if daily_queries > 500:
            advice.append(
                ScalingAdvice(
                    timestamp=now,
                    category="load_pattern",
                    severity="info",
                    title="High query volume",
                    description=f"{daily_queries} queries in the last 24h.",
                    recommendation="Enable aggressive semantic caching (lower threshold to 0.90). Consider read replicas for SQLite.",
                )
            )

        if current_papers > 10000:
            advice.append(
                ScalingAdvice(
                    timestamp=now,
                    category="load_pattern",
                    severity="info",
                    title="Large paper corpus",
                    description=f"{current_papers} papers indexed. BM25 in-memory index growing.",
                    recommendation="Consider sharding ChromaDB collection by year. Schedule BM25 index rebuild off-peak.",
                )
            )

        return advice

    def get_dashboard_data(self, **kwargs) -> dict:
        """Get complete scaling advisor data for the dashboard."""
        return {
            "conferences": self.get_upcoming_conferences(),
            "advice": [
                {
                    "category": a.category,
                    "severity": a.severity,
                    "title": a.title,
                    "description": a.description,
                    "recommendation": a.recommendation,
                }
                for a in self.get_scaling_advice(**kwargs)
            ],
        }


scaling_advisor = ScalingAdvisor()
