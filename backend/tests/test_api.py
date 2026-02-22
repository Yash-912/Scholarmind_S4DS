"""Tests for all FastAPI API endpoints."""


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ScholarMind"


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code in [200, 307]


def test_papers_list(client):
    resp = client.get("/api/papers")
    assert resp.status_code == 200
    data = resp.json()
    assert "papers" in data or "total" in data


def test_search(client):
    resp = client.get("/api/search", params={"q": "machine learning", "top_k": 3})
    assert resp.status_code == 200


def test_topics(client):
    resp = client.get("/api/topics")
    assert resp.status_code == 200


def test_feed(client):
    resp = client.get("/api/feed")
    assert resp.status_code == 200


def test_ingestion_status(client):
    resp = client.get("/api/ingestion/status")
    assert resp.status_code == 200


def test_mlops_models(client):
    resp = client.get("/api/mlops/models")
    assert resp.status_code == 200


def test_aiops_dashboard(client):
    resp = client.get("/api/aiops/dashboard")
    assert resp.status_code == 200


def test_ops_costs(client):
    resp = client.get("/api/ops/costs")
    assert resp.status_code == 200


def test_ops_scaling(client):
    resp = client.get("/api/ops/scaling")
    assert resp.status_code == 200


def test_health_ready(client):
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200


def test_prometheus_metrics(client):
    resp = client.get("/api/health/metrics")
    assert resp.status_code == 200
