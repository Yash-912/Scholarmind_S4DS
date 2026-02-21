"""Tests for LLMOps — prompt registry, routing, cost tracking."""

from app.llmops.prompt_registry import prompt_registry
from app.llmops.router import query_router, QueryComplexity
from app.llmops.cost_tracker import cost_tracker


def test_prompt_registry_loads():
    prompt_registry.load()
    prompts = prompt_registry.list_prompts()
    assert isinstance(prompts, list)


def test_prompt_registry_get_active():
    prompt_registry.load()
    prompt = prompt_registry.get_active("synthesis")
    assert prompt is not None


def test_router_classifies_simple():
    decision = query_router.route("What is attention?")
    assert decision.complexity == QueryComplexity.SIMPLE


def test_router_classifies_complex():
    decision = query_router.route(
        "Compare transformer architectures versus LSTM for long-range dependencies and gap analysis"
    )
    assert decision.complexity == QueryComplexity.COMPLEX


def test_router_returns_model():
    decision = query_router.route("Explain BERT")
    assert decision.model is not None
    assert decision.provider is not None


def test_cost_tracker_summary():
    summary = cost_tracker.get_summary()
    assert isinstance(summary, dict)
    assert "total_cost_usd" in summary or "hourly_spend_usd" in summary
