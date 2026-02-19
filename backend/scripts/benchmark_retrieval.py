"""
Benchmark Retrieval — Measure retrieval recall and latency.
Usage: python -m scripts.benchmark_retrieval
"""

import asyncio
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.retriever import retriever
from app.mlops.experiment_tracker import experiment_tracker


BENCHMARK_QUERIES = [
    "transformer architecture attention mechanism",
    "federated learning privacy preserving",
    "graph neural networks molecular",
    "reinforcement learning robotics control",
    "natural language processing sentiment analysis",
    "computer vision object detection YOLO",
    "generative adversarial networks image synthesis",
    "knowledge graph embedding representation",
    "meta-learning few-shot classification",
    "neural architecture search automl",
]


async def main():
    print(f"Benchmarking retrieval with {len(BENCHMARK_QUERIES)} queries...\n")

    latencies = []
    for query in BENCHMARK_QUERIES:
        # Without reranking
        start = time.time()
        results = await retriever.retrieve(query, top_k=10, rerank=False)
        latency_no_rerank = (time.time() - start) * 1000

        # With reranking
        start = time.time()
        results_reranked = await retriever.retrieve(query, top_k=10, rerank=True)
        latency_reranked = (time.time() - start) * 1000

        print(f"  Query: {query[:50]}...")
        print(f"    No rerank: {len(results)} results in {latency_no_rerank:.0f}ms")
        print(f"    Reranked:  {len(results_reranked)} results in {latency_reranked:.0f}ms")

        latencies.append({
            "query": query,
            "no_rerank_ms": latency_no_rerank,
            "reranked_ms": latency_reranked,
            "results_count": len(results),
        })

    avg_no_rerank = sum(l["no_rerank_ms"] for l in latencies) / len(latencies)
    avg_reranked = sum(l["reranked_ms"] for l in latencies) / len(latencies)

    print(f"\n=== Benchmark Summary ===")
    print(f"  Avg latency (no rerank): {avg_no_rerank:.0f}ms")
    print(f"  Avg latency (reranked):  {avg_reranked:.0f}ms")
    print(f"  Reranker overhead:       {avg_reranked - avg_no_rerank:.0f}ms")


if __name__ == "__main__":
    asyncio.run(main())
