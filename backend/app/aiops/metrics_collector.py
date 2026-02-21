"""
Prometheus Metrics Collector — Defines all application metrics.
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


# ═══ Counters ═══
papers_ingested_total = Counter(
    "scholarmind_papers_ingested_total",
    "Total number of papers ingested",
    ["source"],
)

queries_total = Counter(
    "scholarmind_queries_total",
    "Total number of queries processed",
    ["query_type", "cache_hit"],
)

llm_calls_total = Counter(
    "scholarmind_llm_calls_total",
    "Total number of LLM API calls",
    ["model", "provider", "status"],
)

cache_hits_total = Counter(
    "scholarmind_cache_hits_total",
    "Total semantic cache hits",
)

cache_misses_total = Counter(
    "scholarmind_cache_misses_total",
    "Total semantic cache misses",
)

ingestion_errors_total = Counter(
    "scholarmind_ingestion_errors_total",
    "Total ingestion pipeline errors",
    ["source", "error_type"],
)

# ═══ Histograms ═══
query_latency_seconds = Histogram(
    "scholarmind_query_latency_seconds",
    "Query processing latency",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

embedding_latency_seconds = Histogram(
    "scholarmind_embedding_latency_seconds",
    "Embedding generation latency",
    ["model"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

llm_latency_seconds = Histogram(
    "scholarmind_llm_latency_seconds",
    "LLM API call latency",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

retrieval_latency_seconds = Histogram(
    "scholarmind_retrieval_latency_seconds",
    "Hybrid retrieval latency",
    ["stage"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# ═══ Gauges ═══
vector_db_size = Gauge(
    "scholarmind_vector_db_size",
    "Number of vectors in ChromaDB",
)

active_topics = Gauge(
    "scholarmind_active_topics",
    "Number of active research topics",
)

llm_cost_hourly = Gauge(
    "scholarmind_llm_cost_hourly_usd",
    "LLM cost in USD for the current hour",
)

cache_size = Gauge(
    "scholarmind_cache_size",
    "Number of entries in the semantic cache",
)

cache_hit_rate = Gauge(
    "scholarmind_cache_hit_rate",
    "Cache hit rate (0-1)",
)

model_count = Gauge(
    "scholarmind_registered_models",
    "Number of registered model versions",
)

# ═══ Info ═══
app_info = Info(
    "scholarmind",
    "ScholarMind application info",
)
app_info.info(
    {
        "version": "1.0.0",
        "embedding_model": "allenai/specter2",
        "llm_provider": "groq",
    }
)


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Return the Prometheus content type."""
    return CONTENT_TYPE_LATEST
