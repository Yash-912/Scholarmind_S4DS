# 🔬 ScholarMind — Research Paper Discovery & Synthesis Engine

> An end-to-end **MLOps + LLMOps + AIOps** platform that discovers, indexes, and synthesizes research papers using real-time scraping, semantic search, and LLM-powered multi-paper synthesis.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![Groq](https://img.shields.io/badge/LLM-Groq-orange.svg)](https://groq.com)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND (Vercel / Next.js 15)                              │
│  Chat • Search • Feed • Topics • AIOps Dashboard             │
└──────────────┬───────────────────────────────────────────────┘
               │ REST API
┌──────────────▼───────────────────────────────────────────────┐
│  BACKEND (HuggingFace Spaces / FastAPI)                      │
│                                                              │
│  ┌─ Ingestion ──────────────────────────────────────────┐    │
│  │  arXiv API → PubMed → Semantic Scholar → Dedup       │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌─ Core ML ────────────────────────────────────────────┐    │
│  │  SPECTER2 Embeddings → ChromaDB → Hybrid Retrieval   │    │
│  │  BERTopic → Novelty Detection → Relevance Scoring    │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌─ LLMOps ────────────────────────────────────────────-┐    │
│  │  Groq Gateway → Prompt Registry → Semantic Cache     │    │
│  │  RAG Synthesizer → Hallucination Checker             │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌─ MLOps ─────────────────────────────────────────────-┐    │
│  │  MLflow Registry → Drift Detection (PSI)             │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌─ AIOps ─────────────────────────────────────────────-┐    │
│  │  Health Monitor → Anomaly Detection → Auto-Alerts    │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free: [console.groq.com](https://console.groq.com))
- HuggingFace token (free: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example ../.env
# Edit .env with your API keys

# Seed initial data (fetches ~50 real papers)
python -m app.seed_papers

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/papers` | GET | List/search papers |
| `/api/search?q=...` | GET | Semantic search |
| `/api/synthesis` | POST | RAG multi-paper synthesis |
| `/api/synthesis/stream` | POST | Streaming synthesis (SSE) |
| `/api/topics` | GET | Topic clusters |
| `/api/feed` | GET | Personalized recommendations |
| `/api/ingestion/run` | POST | Trigger paper ingestion |
| `/api/mlops/models` | GET | Model registry |
| `/api/mlops/drift` | GET | Drift detection history |
| `/api/aiops/dashboard` | GET | Full AIOps dashboard |
| `/api/aiops/health` | GET | Health check |

Full interactive docs: `http://localhost:7860/docs`

---

## 🧠 Key Technical Decisions

| Decision | Choice | Why |
|---|---|---|
| **Embedding Model** | SPECTER2 (allenai/specter2) | Domain-specific for scientific papers, 768-dim |
| **Vector DB** | ChromaDB | Persistent, no external service, works on HF Spaces |
| **LLM Provider** | Groq (Mixtral-8x7B) | Free tier, fastest inference (~500 tok/s) |
| **Database** | SQLite (async) | Zero-config, file-based, works everywhere |
| **Topic Model** | BERTopic | State-of-art topic discovery with transformers |
| **Retrieval** | Hybrid (Dense + BM25 + RRF) | Best recall from both paradigms |
| **Re-ranking** | Cross-Encoder (ms-marco) | Precision boost for top-k results |
| **Scheduling** | APScheduler | Lightweight, async-native, no external deps |
| **MLOps** | MLflow | Industry standard, local-first |
| **Drift Detection** | PSI + Cosine Distance | Proven statistical measures |

---

## 🔬 MLOps / LLMOps / AIOps Features

### MLOps
- **Model Registry** — Version, track, and manage embedding/topic/reranker models
- **Experiment Tracking** — MLflow integration for A/B testing retrieval strategies
- **Drift Detection** — Population Stability Index (PSI) on embedding distributions
- **Quality Gates** — Automated evaluation of retrieval recall + synthesis faithfulness

### LLMOps
- **Prompt Registry** — Versioned Jinja2 templates for synthesis, comparison, gap analysis
- **Semantic Cache** — Avoids redundant LLM calls (cosine similarity. > 0.95 = cache hit)
- **Hallucination Detection** — Verifies claims against source papers using a separate LLM
- **Cost Tracking** — Per-model, per-query cost with hourly budget alerts
- **Multi-model Routing** — Auto-fallback from complex → simple models on failure

### AIOps
- **Health Monitoring** — CPU, memory, disk, vector DB, LLM gateway
- **Anomaly Detection** — Memory spikes, vector store failures, cost overruns, low cache hit rates
- **Auto-Alerts** — Cooldown-based alerting with severity levels and remediation suggestions
- **Latency Tracking** — p50/p95/p99 per endpoint

---

## 📦 Deployment

### Backend → HuggingFace Spaces
The backend deploys as a Docker-based HF Space:
```bash
cd backend
# Push to HF Spaces (set HF_TOKEN)
huggingface-cli login
huggingface-cli repo create scholarmind --type space --space-sdk docker
git push hf main
```

### Frontend → Vercel
```bash
cd frontend
vercel deploy
```

---

## 📁 Project Structure

```
scholarmind/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings (Pydantic)
│   │   ├── seed_papers.py       # Initial data seeding
│   │   ├── api/
│   │   │   ├── dependencies.py  # DI (DB session, user)
│   │   │   └── routes/          # 8 route modules
│   │   ├── core/                # ML: embeddings, retrieval, topics
│   │   ├── db/                  # SQLAlchemy models + CRUD
│   │   ├── ingestion/           # Scrapers + pipeline
│   │   ├── llmops/              # LLM gateway, prompts, cache
│   │   ├── mlops/               # Model registry, drift
│   │   └── aiops/               # Health monitor, alerts
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh
├── frontend/                    # Next.js 15 app
├── .env.example
├── .gitignore
└── README.md
```
