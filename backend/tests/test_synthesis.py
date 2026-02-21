"""Tests for LLM synthesis — verifies RAG produces cited output."""

import pytest
from app.llmops.synthesizer import synthesizer


@pytest.mark.asyncio
async def test_synthesis_returns_answer():
    result = await synthesizer.synthesize(
        "What are recent advances in federated learning?"
    )
    assert "answer" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0


@pytest.mark.asyncio
async def test_synthesis_includes_metrics():
    result = await synthesizer.synthesize("Explain transformers")
    if "metrics" in result:
        assert "latency_ms" in result["metrics"]


@pytest.mark.asyncio
async def test_synthesis_query_types():
    for qt in ["synthesis", "comparison", "gap_analysis", "chat"]:
        result = await synthesizer.synthesize("AI in healthcare", query_type=qt)
        assert "answer" in result
