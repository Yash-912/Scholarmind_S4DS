"""
Semantic Cache — Avoids redundant LLM calls for similar queries.
Uses embedding similarity to detect near-duplicate queries.
"""

import numpy as np
import time
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import OrderedDict

from app.core.embeddings import embedding_service
from app.config import settings


@dataclass
class CacheEntry:
    """A cached query-response pair."""

    query: str
    query_embedding: np.ndarray
    response: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hit_count: int = 0


class SemanticCache:
    """
    LRU semantic cache using embedding similarity.
    If a new query has cosine similarity > threshold to a cached query,
    return the cached response.
    """

    def __init__(self, max_size: int = 500, threshold: float = None):
        self.max_size = max_size
        self.threshold = threshold or settings.CACHE_SIMILARITY_THRESHOLD
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def get(self, query: str) -> Optional[dict]:
        """
        Check if a similar query is cached.

        Returns:
            Cached response dict if found, None if cache miss.
        """
        if not self._cache:
            self._misses += 1
            return None

        # Embed the query
        query_embedding = embedding_service.embed_query(query)

        # Check similarity against all cached queries
        best_sim = 0.0
        best_key = None

        for key, entry in self._cache.items():
            sim = self._cosine_sim(query_embedding, entry.query_embedding)
            if sim > best_sim:
                best_sim = sim
                best_key = key

        if best_sim >= self.threshold and best_key:
            self._hits += 1
            entry = self._cache[best_key]
            entry.hit_count += 1
            # Move to end (LRU)
            self._cache.move_to_end(best_key)
            print(f"💾 Cache HIT (sim={best_sim:.3f}): {query[:50]}...")
            return entry.response

        self._misses += 1
        return None

    def put(self, query: str, response: dict):
        """
        Cache a query-response pair.
        """
        # Embed the query
        query_embedding = embedding_service.embed_query(query)

        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        key = f"cache_{len(self._cache)}_{time.time()}"
        self._cache[key] = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            response=response,
        )

    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(total, 1), 3),
            "threshold": self.threshold,
        }


# Global singleton
semantic_cache = SemanticCache()
