"""
Generate Topics — One-off script to train the topic model.
Usage: python -m scripts.generate_topics
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_session
from app.db import crud
from app.core.embeddings import embedding_service
from app.core.topic_model import TopicModeler
from app.mlops.experiment_tracker import experiment_tracker
import time


async def main():
    print("Loading papers from database...")

    async with async_session() as session:
        papers = await crud.get_papers(session, skip=0, limit=5000)

    if not papers:
        print("No papers found. Run seed_papers.py first.")
        return

    print(f"Loaded {len(papers)} papers. Generating embeddings...")

    texts = [f"{p.title}. {p.abstract or ''}" for p in papers]
    embeddings = embedding_service.embed_texts(texts)

    print(f"Training BERTopic model on {len(embeddings)} documents...")
    start = time.time()

    modeler = TopicModeler()
    topics = modeler.fit(embeddings, texts)
    duration = time.time() - start

    print("\n=== Topic Model Results ===")
    print(f"  Topics discovered: {len(topics)}")
    print(f"  Training time: {duration:.1f}s")

    for t in topics[:10]:
        print(f"  Topic {t['id']}: {t['name']} ({t['count']} papers)")
        print(f"    Keywords: {', '.join(t.get('keywords', [])[:5])}")

    # Log to MLflow
    experiment_tracker.log_topic_modeling(
        num_topics=len(topics),
        num_documents=len(papers),
        coherence_score=0.0,
        duration_seconds=duration,
    )

    print("\n✅ Topic model trained and logged.")


if __name__ == "__main__":
    asyncio.run(main())
