# ScholarMind — API Reference

Base URL: `http://localhost:7860` (local) or `https://your-space.hf.space` (production)

Full interactive docs available at: `/docs` (Swagger UI)

---

## Papers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/papers` | List papers (paginated) |
| GET | `/api/papers/{id}` | Get paper by ID |
| GET | `/api/papers/{id}/related` | Get related papers |

## Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/search` | Hybrid semantic + keyword search |

**Body:** `{ "query": "string", "top_k": 10, "rerank": true }`

## Synthesis (RAG)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/synthesis/synthesize` | Multi-paper RAG synthesis |
| POST | `/api/synthesis/compare` | Compare papers |
| POST | `/api/synthesis/stream` | Streaming synthesis (SSE) |

**Body:** `{ "query": "string", "query_type": "synthesis|comparison|gap_analysis|chat", "top_k": 10 }`

## Topics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/topics` | List all topics |
| GET | `/api/topics/trending` | Get trending topics |
| GET | `/api/topics/{id}` | Get topic details |

## Feed

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/feed` | Personalized paper feed |
| POST | `/api/feed/interests` | Update user interests |
| POST | `/api/feed/bookmark` | Bookmark a paper |

## Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingestion/trigger` | Trigger ingestion manually |
| GET | `/api/ingestion/status` | Get pipeline status |

## MLOps

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/mlops/models` | Model registry |
| GET | `/api/mlops/drift` | Drift detection data |

## AIOps

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/aiops/dashboard` | Full AIOps dashboard |
| POST | `/api/aiops/resolve/{id}` | Resolve an alert |

## Ops Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ops/models` | Models + monitoring |
| GET | `/api/ops/costs` | LLM cost data |
| GET | `/api/ops/drift` | Drift history |
| GET | `/api/ops/alerts` | All alerts |
| GET | `/api/ops/anomalies` | Detected anomalies |
| GET | `/api/ops/remediation` | Remediation actions |
| GET | `/api/ops/cache` | Semantic cache stats |
| GET | `/api/ops/scaling` | Scaling advice + conferences |
| GET | `/api/ops/prompts` | Prompt templates |
| GET | `/api/ops/quality-gate` | Quality gate baselines |

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Liveness check |
| GET | `/api/health/ready` | Readiness check |
| GET | `/api/health/components` | Component health |
| GET | `/api/health/metrics` | Prometheus metrics |
