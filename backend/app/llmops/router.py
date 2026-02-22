"""
Query Router — Classifies query complexity and routes to the appropriate LLM tier.
"""

from enum import Enum
from dataclasses import dataclass
from app.config import settings


class QueryComplexity(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


@dataclass
class RoutingDecision:
    complexity: QueryComplexity
    model: str
    provider: str
    estimated_cost_usd: float
    estimated_latency_ms: int
    reasoning: str


# Keyword signals for complexity detection
_COMPLEX_SIGNALS = [
    "compare",
    "contrast",
    "versus",
    "differences between",
    "gap analysis",
    "research gaps",
    "systematic review",
    "meta-analysis",
    "comprehensive",
    "evolution of",
    "how has",
    "timeline",
    "history of advances",
]

_SIMPLE_SIGNALS = [
    "what is",
    "define",
    "explain",
    "summarize",
    "who wrote",
    "when was",
    "list",
]


class QueryRouter:
    """Routes queries to the optimal LLM tier based on complexity."""

    # Model tiers: (model_name, provider, cost_per_1k_tokens, avg_latency_ms)
    TIERS = {
        QueryComplexity.SIMPLE: {
            "model": "llama-3.1-8b-instant",
            "provider": "groq",
            "cost_per_1k": 0.00005,
            "avg_latency_ms": 300,
        },
        QueryComplexity.STANDARD: {
            "model": settings.DEFAULT_SYNTHESIS_MODEL,
            "provider": "groq",
            "cost_per_1k": 0.00027,
            "avg_latency_ms": 800,
        },
        QueryComplexity.COMPLEX: {
            "model": "llama-3.3-70b-versatile",
            "provider": "groq",
            "cost_per_1k": 0.00059,
            "avg_latency_ms": 2000,
        },
    }

    async def route(self, query: str, query_type: str | None = None) -> RoutingDecision:
        """Classify query and return routing decision."""
        complexity = await self._classify(query, query_type)
        tier = self.TIERS[complexity]

        estimated_tokens = self._estimate_tokens(query, complexity)

        return RoutingDecision(
            complexity=complexity,
            model=tier["model"],
            provider=tier["provider"],
            estimated_cost_usd=tier["cost_per_1k"] * estimated_tokens / 1000,
            estimated_latency_ms=tier["avg_latency_ms"],
            reasoning=self._explain(query, complexity),
        )

    async def _classify(self, query: str, query_type: str | None = None) -> QueryComplexity:
        """Determine query complexity using LLM instead of naive keywords."""
        if query_type in ("comparison", "gap_analysis"):
            return QueryComplexity.COMPLEX
        if query_type == "chat":
            return QueryComplexity.SIMPLE

        try:
            from app.llmops.gateway import llm_gateway
            prompt = f"Analyze query complexity. Return EXACTLY ONE WORD from [SIMPLE, STANDARD, COMPLEX]. Query: {query}"
            resp = await llm_gateway.generate(prompt, model="llama-3.1-8b-instant", max_tokens=10)
            txt = resp["text"].upper()
            if "COMPLEX" in txt:
                return QueryComplexity.COMPLEX
            if "SIMPLE" in txt:
                return QueryComplexity.SIMPLE
        except Exception:
            pass
        return QueryComplexity.STANDARD

    def _estimate_tokens(self, query: str, complexity: QueryComplexity) -> int:
        """Rough token estimate for the full request (prompt + response)."""
        base = len(query.split()) * 2  # input
        if complexity == QueryComplexity.SIMPLE:
            return base + 300
        elif complexity == QueryComplexity.STANDARD:
            return base + 800
        else:
            return base + 1500

    def _explain(self, query: str, complexity: QueryComplexity) -> str:
        q_lower = query.lower()
        reasons = []
        if complexity == QueryComplexity.COMPLEX:
            for s in _COMPLEX_SIGNALS:
                if s in q_lower:
                    reasons.append(f"contains '{s}'")
            return f"Complex — {', '.join(reasons) or 'multi-part query'}"
        elif complexity == QueryComplexity.SIMPLE:
            return "Simple — short, factual query"
        return "Standard — moderate synthesis required"


query_router = QueryRouter()
