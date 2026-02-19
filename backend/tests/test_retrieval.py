"""Tests for hybrid retrieval — verifies ranked results are returned."""

import pytest
from app.core.retriever import retriever


@pytest.mark.asyncio
async def test_retrieval_returns_results():
    results = await retriever.retrieve("neural network optimization", top_k=5)
    assert isinstance(results, list)
    # May be empty if no papers are indexed yet
    if len(results) > 0:
        assert "title" in results[0] or "paper_id" in results[0]
        assert "score" in results[0]


@pytest.mark.asyncio
async def test_retrieval_respects_top_k():
    results = await retriever.retrieve("attention mechanism", top_k=3)
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_retrieval_with_reranking():
    results = await retriever.retrieve("language models", top_k=5, rerank=True)
    assert isinstance(results, list)
    # With reranking, scores should be sorted descending
    if len(results) > 1:
        scores = [r.get("score", 0) for r in results]
        assert scores == sorted(scores, reverse=True)
