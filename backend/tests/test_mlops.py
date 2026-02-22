"""Tests for MLOps — model registry, drift detection, quality gate."""

import pytest
from app.mlops.registry import model_registry
from app.mlops.drift_detector import drift_detector
from app.mlops.quality_gate import quality_gate
from app.mlops.model_monitor import model_monitor


@pytest.mark.asyncio
async def test_registry_list_models():
    models = await model_registry.list_models()
    assert isinstance(models, list)


@pytest.mark.asyncio
async def test_drift_detector_get_history():
    history = await drift_detector.get_drift_history()
    assert isinstance(history, (list, dict))


def test_quality_gate_pass():
    result = quality_gate.check("retrieval_recall@10", 0.70)
    assert result.passed is True


def test_quality_gate_fail():
    result = quality_gate.check("retrieval_recall@10", 0.50)
    assert result.passed is False


def test_model_monitor_record():
    model_monitor.record("specter2", "latency_ms", 150.0)
    stats = model_monitor.get_stats("specter2", "latency_ms")
    assert stats["count"] == 1
    assert stats["latest"] == 150.0
