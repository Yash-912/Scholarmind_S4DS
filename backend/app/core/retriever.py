"""
Hybrid Retriever — Combines dense (vector) and sparse (BM25) retrieval
with Reciprocal Rank Fusion.
"""

import numpy as np
from rank_bm25 import BM25Okapi
from dataclasses import dataclass
import time

from app.core.embeddings import embedding_service
from app.core.vector_store import vector_store


@dataclass
class RetrievedPaper:
    """A paper retrieved by the retrieval system."""
    paper_id: str
    title: str
    text: str
    score: float
    source: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Dense retrieval (ChromaDB cosine similarity)
    2. Sparse retrieval (BM25)
    3. Reciprocal Rank Fusion to merge results
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k  # RRF constant
        self._bm25_corpus = []
        self._bm25_ids = []
        self._bm25_docs = []
        self._bm25_index = None
        self._bm25_built = False

    def build_bm25_index(self, paper_ids: list[str], texts: list[str]):
        """Build the BM25 index from paper texts."""
        start = time.time()
        self._bm25_ids = paper_ids
        self._bm25_docs = texts
        tokenized = [text.lower().split() for text in texts]
        self._bm25_index = BM25Okapi(tokenized)
        self._bm25_built = True
        elapsed = time.time() - start
        print(f"📊 BM25 index built: {len(texts)} documents in {elapsed:.2f}s")

    def _sparse_search(self, query: str, top_k: int = 100) -> list[tuple[str, float]]:
        """BM25 sparse retrieval."""
        if not self._bm25_built or not self._bm25_index:
            return []

        tokenized_query = query.lower().split()
        scores = self._bm25_index.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self._bm25_ids[idx], float(scores[idx])))

        return results

    async def retrieve(
        self,
        query: str,
        top_k: int = 15,
        dense_top_k: int = 100,
        sparse_top_k: int = 100,
        use_bm25: bool = True,
    ) -> list[RetrievedPaper]:
        """
        Hybrid retrieval with RRF fusion.

        Args:
            query: Search query
            top_k: Final number of results
            dense_top_k: Dense retrieval candidates
            sparse_top_k: Sparse retrieval candidates
            use_bm25: Whether to include BM25 results

        Returns:
            List of RetrievedPaper sorted by fused score
        """
        start = time.time()

        # 1. Dense retrieval
        query_embedding = embedding_service.embed_query(query)
        dense_results = vector_store.search(query_embedding, top_k=dense_top_k)

        dense_ranked = []
        if dense_results and dense_results["ids"] and dense_results["ids"][0]:
            for i, doc_id in enumerate(dense_results["ids"][0]):
                distance = dense_results["distances"][0][i] if dense_results["distances"] else 0
                score = 1 - distance  # Convert distance to similarity
                dense_ranked.append((doc_id, score))

        # 2. Sparse retrieval (BM25)
        sparse_ranked = []
        if use_bm25 and self._bm25_built:
            sparse_ranked = self._sparse_search(query, top_k=sparse_top_k)

        # 3. Reciprocal Rank Fusion
        fused_scores = {}

        for rank, (doc_id, _) in enumerate(dense_ranked):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (self.rrf_k + rank + 1)

        for rank, (doc_id, _) in enumerate(sparse_ranked):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (self.rrf_k + rank + 1)

        # Sort by fused score
        sorted_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Build result objects
        results = []
        # Create lookup from dense results
        dense_lookup = {}
        if dense_results and dense_results["ids"] and dense_results["ids"][0]:
            for i, doc_id in enumerate(dense_results["ids"][0]):
                dense_lookup[doc_id] = {
                    "document": dense_results["documents"][0][i] if dense_results["documents"] else "",
                    "metadata": dense_results["metadatas"][0][i] if dense_results["metadatas"] else {},
                }

        for doc_id, score in sorted_ids:
            info = dense_lookup.get(doc_id, {})
            metadata = info.get("metadata", {})
            results.append(RetrievedPaper(
                paper_id=doc_id,
                title=metadata.get("title", ""),
                text=info.get("document", ""),
                score=score,
                source=metadata.get("source", ""),
                metadata=metadata,
            ))

        elapsed = time.time() - start
        print(f"🔍 Hybrid retrieval: {len(results)} results in {elapsed*1000:.0f}ms (dense={len(dense_ranked)}, sparse={len(sparse_ranked)})")

        return results


# Global singleton
retriever = HybridRetriever()
