"""
ScholarMind — Research Paper Discovery & Synthesis Engine

Main FastAPI application entry point.
"""

import os
import sys

# === Fix Windows DLL loading order (only needed on Windows with Anaconda + torch) ===
if os.name == "nt":
    torch_lib_path = os.path.join(
        os.path.dirname(sys.executable), "Lib", "site-packages", "torch", "lib"
    )
    if os.path.isdir(torch_lib_path):
        os.add_dll_directory(torch_lib_path)
# === End DLL fix ===

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from app.config import settings
from app.db.database import init_database
from app.core.vector_store import vector_store
from app.llmops.gateway import llm_gateway
from app.llmops.prompt_registry import prompt_registry
from app.ingestion.scheduler import start_scheduler, stop_scheduler
from app.mlops.registry import model_registry
from app.aiops.health_monitor import health_monitor

# Import route modules
from app.api.routes import (
    papers,
    synthesis,
    search,
    topics,
    feed,
    ingestion,
    mlops,
    aiops,
    health,
    ops,
)
from app.mlops.experiment_tracker import experiment_tracker
from app.aiops.alerts import alert_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    print(f"\n{'=' * 60}")
    print(f"🚀 ScholarMind v{settings.APP_VERSION} Starting...")
    print(f"{'=' * 60}\n")

    # 1. Initialize database
    await init_database()

    # 2. Create data directories
    os.makedirs("data/chroma", exist_ok=True)
    os.makedirs("data/mlflow", exist_ok=True)
    os.makedirs("data/cache", exist_ok=True)

    # 3. Initialize vector store
    vector_store.initialize()

    # 4. Initialize LLM gateway
    llm_gateway.initialize()

    # 5. Load prompt templates
    prompt_registry.load()

    # 6. Initialize MLflow
    model_registry.initialize()

    # 6b. Initialize experiment tracker
    experiment_tracker.initialize()

    # 6c. Initialize alert rules
    alert_engine.add_default_rules(health_monitor=health_monitor)

    # 7. Load embedding model (lazy — loads on first use)
    print("📝 Embedding model will load on first use (lazy initialization)")

    # 8. Start ingestion scheduler
    start_scheduler()

    print(f"\n{'=' * 60}")
    print("✅ ScholarMind Ready — http://0.0.0.0:7860")
    print("📚 API Docs — http://0.0.0.0:7860/docs")
    print(f"{'=' * 60}\n")

    yield

    # Shutdown
    print("\n🛑 ScholarMind shutting down...")
    stop_scheduler()


# Create FastAPI app
app = FastAPI(
    title="ScholarMind",
    description="Research Paper Discovery & Synthesis Engine — MLOps + LLMOps + AIOps",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Latency tracking middleware
@app.middleware("http")
async def track_latency(request: Request, call_next):
    import time
    from app.aiops.health_monitor import health_monitor
    from app.aiops.metrics_collector import query_latency_seconds
    from app.aiops.anomaly_detector import anomaly_detector
    
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    
    # Record stage-level tracking
    health_monitor.record_latency(request.url.path, elapsed)
    
    # Wire Prometheus Metrics & Anomaly Detector
    query_latency_seconds.labels(endpoint=request.url.path).observe(elapsed / 1000.0)
    anomaly_detector.record(f"latency_{request.url.path.replace('/', '_')}", elapsed)
    
    response.headers["X-Response-Time"] = f"{elapsed:.0f}ms"
    return response

# Connect scheduler to proactively poll health check
from apscheduler.schedulers.asyncio import AsyncIOScheduler
proactive_scheduler = AsyncIOScheduler()
@proactive_scheduler.scheduled_job("interval", minutes=1)
async def scheduled_health_check():
    from app.aiops.health_monitor import health_monitor
    await health_monitor.collect_metrics()
    
@app.on_event("startup")
async def start_proactive_monitoring():
    proactive_scheduler.start()

@app.on_event("shutdown")
async def stop_proactive_monitoring():
    proactive_scheduler.shutdown()



# Register route modules
app.include_router(papers.router, prefix="/api")
app.include_router(synthesis.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(feed.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(mlops.router, prefix="/api")
app.include_router(aiops.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(ops.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ScholarMind",
        "version": settings.APP_VERSION,
        "description": "Research Paper Discovery & Synthesis Engine",
        "docs": "/docs",
        "endpoints": {
            "papers": "/api/papers",
            "search": "/api/search",
            "synthesis": "/api/synthesis",
            "topics": "/api/topics",
            "feed": "/api/feed",
            "ingestion": "/api/ingestion",
            "mlops": "/api/mlops",
            "aiops": "/api/aiops",
            "health": "/api/health",
            "ops": "/api/ops",
        },
    }


@app.get("/api/health")
async def health():
    """Quick health check."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
