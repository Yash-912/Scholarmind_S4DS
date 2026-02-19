"""Tests for all FastAPI API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ScholarMind"


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code in [200, 307]


def test_papers_list():
    resp = client.get("/api/papers")
    assert resp.status_code == 200
    data = resp.json()
    assert "papers" in data or "total" in data


def test_search():
    resp = client.post("/api/search", json={"query": "machine learning", "top_k": 3})
    assert resp.status_code == 200


def test_topics():
    resp = client.get("/api/topics")
    assert resp.status_code == 200


def test_feed():
    resp = client.get("/api/feed")
    assert resp.status_code == 200


def test_ingestion_status():
    resp = client.get("/api/ingestion/status")
    assert resp.status_code == 200


def test_mlops_models():
    resp = client.get("/api/mlops/models")
    assert resp.status_code == 200


def test_aiops_dashboard():
    resp = client.get("/api/aiops/dashboard")
    assert resp.status_code == 200


def test_ops_costs():
    resp = client.get("/api/ops/costs")
    assert resp.status_code == 200


def test_ops_scaling():
    resp = client.get("/api/ops/scaling")
    assert resp.status_code == 200


def test_health_ready():
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200


def test_prometheus_metrics():
    resp = client.get("/api/health/metrics")
    assert resp.status_code == 200
