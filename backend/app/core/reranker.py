"""
Cross-Encoder Re-ranker — Re-ranks retrieved results for higher precision.
"""

import time
from typing import Optional


class Reranker:
    """Cross-encoder re-ranker for improving retrieval precision."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._loaded = False

    def load(self):
        """Load the cross-encoder model."""
        if self._loaded:
            return

        print(f"🔄 Loading re-ranker: {self.model_name}")
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            self._loaded = True
            print(f"✅ Re-ranker loaded")
        except Exception as e:
            print(f"⚠️ Re-ranker load failed: {e}")
            self._loaded = False

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 10,
    ) -> list[dict]:
        """
        Re-rank documents using the cross-encoder.

        Args:
            query: Search query
            documents: List of dicts with at least 'text' key
            top_k: Number of top results to return

        Returns:
            Re-ranked list of documents with added 'rerank_score'
        """
        if not self._loaded:
            self.load()

        if not self._loaded or not documents:
            return documents[:top_k]

        start = time.time()

        # Create query-document pairs
        pairs = [(query, doc.get("text", "")) for doc in documents]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Attach scores and sort
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        reranked = sorted(documents, key=lambda x: x.get("rerank_score", 0), reverse=True)

        elapsed = time.time() - start
        print(f"♻️ Re-ranked {len(documents)} → top {top_k} in {elapsed*1000:.0f}ms")

        return reranked[:top_k]

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Global singleton
reranker = Reranker()
