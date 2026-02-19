# ScholarMind — System Architecture

## Overview

ScholarMind is a full-stack **Research Paper Discovery & Synthesis Engine** with production-grade MLOps, LLMOps, and AIOps.

```
┌──────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
│  Landing │ Search │ Chat │ Feed │ Topics │ Papers │ Dashboard│
│                    ↕ REST API calls                          │
├──────────────────────────────────────────────────────────────┤
│                      API LAYER (FastAPI)                      │
│  Papers │ Search │ Synthesis │ Topics │ Feed │ Ingest │ Ops  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  INGESTION   │  │   CORE ML    │  │     LLMOps       │   │
│  │  Pipeline    │  │              │  │                  │   │
│  │  • arXiv     │  │  • SPECTER2  │  │  • Groq Gateway  │   │
│  │  • PubMed    │  │  • ChromaDB  │  │  • Prompt Reg.   │   │
│  │  • S2 API    │  │  • Hybrid    │  │  • Sem. Cache    │   │
│  │  • Dedup     │  │    Retriever │  │  • Halluc. Check │   │
│  │  • Scheduler │  │  • Reranker  │  │  • Cost Tracker  │   │
│  │              │  │  • BERTopic  │  │  • Evaluator     │   │
│  │              │  │  • Novelty   │  │  • Query Router  │   │
│  │              │  │  • Relevance │  │                  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌──────────────────────────────────────┐  │
│  │    MLOps     │  │             AIOps                    │  │
│  │  • MLflow    │  │  • Prometheus Metrics                │  │
│  │  • Registry  │  │  • Health Monitor                    │  │
│  │  • Drift     │  │  • Anomaly Detector (IsolationForest)│  │
│  │  • Quality   │  │  • Auto Remediation                  │  │
│  │    Gate      │  │  • Alert Engine                      │  │
│  │  • Monitor   │  │  • Scaling Advisor                   │  │
│  └─────────────┘  └──────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              DATA LAYER                               │   │
│  │  SQLite (async) │ ChromaDB (vectors) │ MLflow (exps) │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### Ingestion Pipeline
```
arXiv API → Scraper → Parser → Dedup → Embeddings → ChromaDB + SQLite
PubMed API ↗                                         ↑
S2 API ↗                                    (SPECTER2 768-dim)
```

### Query Processing (RAG)
```
User Query → Router → Retriever (Dense + Sparse) → RRF Merge
                                → Reranker → Context Assembly
                                → LLM (Groq) → Hallucination Check
                                → Response + Metrics
```

### Monitoring
```
Every API call → Latency Tracking → Prometheus Metrics
                                  → Anomaly Detection
                                  → Alert Engine → Auto Remediation
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | SQLite (async via aiosqlite) |
| Vector DB | ChromaDB (in-process, persistent) |
| Embeddings | SPECTER2 (allenai/specter2) via sentence-transformers |
| LLM | Groq API (Mixtral-8x7B, Llama 3) |
| Topic Model | BERTopic (UMAP + HDBSCAN) |
| Experiment Tracking | MLflow (local) |
| Metrics | Prometheus client library |
| Scheduling | APScheduler |
| CI/CD | GitHub Actions → HF Spaces + Vercel |
