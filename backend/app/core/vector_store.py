"""
Vector Store — ChromaDB wrapper for paper embeddings.
Handles collection management, insertion, search, and stats.
"""

import chromadb
import numpy as np
from typing import Optional
from app.config import settings
import os
import time


class VectorStore:
    """ChromaDB vector store for paper embeddings."""

    def __init__(self, persist_dir: str = None, collection_name: str = "papers"):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialized = False

    def initialize(self):
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return

        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._initialized = True
        print(
            f"✅ ChromaDB initialized at {self.persist_dir} (collection: {self.collection_name}, count: {self.collection.count()})"
        )

    def add_papers(
        self,
        ids: list[str],
        embeddings: list[list[float]] | np.ndarray,
        documents: list[str],
        metadatas: list[dict],
    ):
        """
        Add papers to the vector store.

        Args:
            ids: Unique IDs for each paper
            embeddings: Embedding vectors
            documents: Paper text (title + abstract)
            metadatas: Metadata dicts for filtering
        """
        if not self._initialized:
            self.initialize()

        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()

        # ChromaDB has a batch size limit, process in chunks
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]
            batch_docs = documents[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]

            self.collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_docs,
                metadatas=batch_meta,
            )

        print(f"📦 Added/updated {len(ids)} papers in vector store")

    def search(
        self,
        query_embedding: list[float] | np.ndarray,
        top_k: int = 20,
        where: Optional[dict] = None,
    ) -> dict:
        """
        Search for similar papers.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            where: Optional metadata filter

        Returns:
            ChromaDB query results dict
        """
        if not self._initialized:
            self.initialize()

        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        start = time.time()

        # Guard: empty collection → return empty results immediately
        doc_count = self.collection.count()
        if doc_count == 0:
            return {
                "ids": [[]],
                "documents": [[]],
                "distances": [[]],
                "metadatas": [[]],
            }

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, doc_count),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)
        elapsed = time.time() - start

        print(
            f"🔍 Vector search: {len(results['ids'][0]) if results['ids'] else 0} results in {elapsed * 1000:.0f}ms"
        )
        return results

    def delete(self, ids: list[str]):
        """Delete papers by ID."""
        if not self._initialized:
            self.initialize()
        self.collection.delete(ids=ids)

    def get_stats(self) -> dict:
        """Get vector store statistics."""
        if not self._initialized:
            self.initialize()

        count = self.collection.count()
        return {
            "total_vectors": count,
            "collection_name": self.collection_name,
            "persist_dir": self.persist_dir,
        }

    @property
    def count(self) -> int:
        if not self._initialized:
            self.initialize()
        return self.collection.count()


# Global singleton
vector_store = VectorStore()
