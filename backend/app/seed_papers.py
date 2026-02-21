"""
Seed script — Runs an initial ingestion to populate the database.
Usage: python -m app.seed_papers
"""

import asyncio
import sys
import os

# === Fix Windows DLL loading order (must be BEFORE any torch import) ===
torch_lib_path = os.path.join(
    os.path.dirname(sys.executable),
    "Lib",
    "site-packages",
    "torch",
    "lib"
)
if os.path.isdir(torch_lib_path):
    os.add_dll_directory(torch_lib_path)
# === End DLL fix ===

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def seed():
    """Run initial ingestion with a small batch."""
    from app.db.database import init_database
    from app.core.vector_store import vector_store
    from app.core.embeddings import embedding_service
    from app.llmops.gateway import llm_gateway
    from app.ingestion.pipeline import run_ingestion_pipeline
    from app.mlops.registry import model_registry

    print("🌱 Seeding ScholarMind database...")

    # Initialize
    await init_database()
    vector_store.initialize()
    llm_gateway.initialize()
    model_registry.initialize()

    # Load embedding model eagerly for seeding
    embedding_service.load()

    # Register initial model versions
    await model_registry.register_model(
        name="specter2",
        version="1.0.0",
        model_type="embedding",
        metrics={"dimension": embedding_service.dimension},
        parameters={"model_name": embedding_service.model_name},
    )

    # Run ingestion with small batches
    result = await run_ingestion_pipeline(
        sources=["arxiv", "pubmed"],
        max_arxiv=30,
        max_pubmed=20,
    )

    print("\n🌱 Seeding complete!")
    print(f"   Papers ingested: {result.get('papers_new', 0)}")
    print(f"   Vectors stored: {vector_store.count}")

    return result


if __name__ == "__main__":
    asyncio.run(seed())
