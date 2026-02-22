"""Tests for LLMOps — prompt registry, routing, cost tracking."""

from app.llmops.prompt_registry import prompt_registry
import pytest
from unittest.mock import patch, AsyncMock
from app.llmops.router import query_router, QueryComplexity
from app.llmops.cost_tracker import cost_tracker


def test_prompt_registry_loads():
    prompt_registry.load()
    prompts = prompt_registry.list_templates()
    assert isinstance(prompts, list)


def test_prompt_registry_get_template():
    prompt_registry.load()
    prompt = prompt_registry.get_template("synthesis")
    assert prompt is not None


@pytest.mark.asyncio
@patch("app.llmops.gateway.llm_gateway.generate", new_callable=AsyncMock)
async def test_router_classifies_simple(mock_generate):
    mock_generate.return_value = {"text": "SIMPLE"}
    decision = await query_router.route("What is attention?")
    assert decision.complexity == QueryComplexity.SIMPLE


@pytest.mark.asyncio
@patch("app.llmops.gateway.llm_gateway.generate", new_callable=AsyncMock)
async def test_router_classifies_complex(mock_generate):
    mock_generate.return_value = {"text": "COMPLEX"}
    decision = await query_router.route(
        "Compare transformer architectures versus LSTM for long-range dependencies and gap analysis"
    )
    assert decision.complexity == QueryComplexity.COMPLEX


@pytest.mark.asyncio
@patch("app.llmops.gateway.llm_gateway.generate", new_callable=AsyncMock)
async def test_router_returns_model(mock_generate):
    mock_generate.return_value = {"text": "STANDARD"}
    decision = await query_router.route("Explain BERT")
    assert decision.model is not None
    assert decision.provider is not None


def test_cost_tracker_summary():
    summary = cost_tracker.get_summary()
    assert isinstance(summary, dict)
    assert "total_cost_usd" in summary or "hourly_spend_usd" in summary
