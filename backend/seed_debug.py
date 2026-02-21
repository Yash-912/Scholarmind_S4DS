"""Debug seeding with full traceback."""
import asyncio
import sys
import os
import traceback

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    try:
        from app.db.database import init_database
        from app.core.vector_store import vector_store
        from app.core.embeddings import embedding_service
        from app.llmops.gateway import llm_gateway
        from app.mlops.registry import model_registry

        print("Seeding ScholarMind database...")
        await init_database()
        vector_store.initialize()
        llm_gateway.initialize()
        model_registry.initialize()
        embedding_service.load()

        # Register model
        print("Registering model...")
        await model_registry.register_model(
            name="specter2",
            version="1.0.0",
            model_type="embedding",
            metrics={"dimension": embedding_service.dimension},
            parameters={"model_name": embedding_service.model_name},
        )
        print("Model registered OK")

        # Run ingestion
        print("Running ingestion...")
        from app.ingestion.pipeline import run_ingestion_pipeline
        result = await run_ingestion_pipeline(
            sources=["arxiv", "pubmed"],
            max_arxiv=30,
            max_pubmed=20,
        )
        print(f"Seeding complete! Papers: {result.get('papers_new', 0)}")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
