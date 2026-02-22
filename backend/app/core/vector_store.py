"""
Vector Store — ChromaDB wrapper for paper embeddings.
Handles collection management, insertion, search, and stats.
"""

import chromadb
import numpy as np
import json
from typing import Optional
from sqlalchemy import text
from app.config import settings
from app.db.database import async_session, engine, is_postgres
import os
import time


class VectorStore:
    """Hybrid Vector Store supporting PgVector (Production) and ChromaDB (Local Dev)."""

    def __init__(self, persist_dir: str = None, collection_name: str = "papers"):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name
        self._initialized = False
        self.is_pg = is_postgres
        self.client = None
        self.collection = None

    async def initialize(self):
        """Initialize appropriate backend (PgVector vs ChromaDB)."""
        if self._initialized:
            return

        if self.is_pg:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.execute(
                    text(f"""
                    CREATE TABLE IF NOT EXISTS {self.collection_name} (
                        id VARCHAR(255) PRIMARY KEY,
                        embedding vector({settings.EMBEDDING_DIM}),
                        document TEXT,
                        metadata JSONB
                    )
                """)
                )
                try:
                    await conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS idx_{self.collection_name}_emb "
                            f"ON {self.collection_name} USING hnsw (embedding vector_cosine_ops)"
                        )
                    )
                except Exception:
                    pass
            print(f"✅ PgVector initialized (table: {self.collection_name})")
        else:
            os.makedirs(self.persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            print(
                f"✅ ChromaDB initialized at {self.persist_dir} (collection: {self.collection_name})"
            )

        self._initialized = True

    async def add_papers(
        self,
        ids: list[str],
        embeddings: list[list[float]] | np.ndarray,
        documents: list[str],
        metadatas: list[dict],
    ):
        """Add papers uniformly regardless of backend."""
        if not self._initialized:
            await self.initialize()

        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()

        if self.is_pg:
            async with async_session() as session:
                for i in range(len(ids)):
                    params = {
                        "id": ids[i],
                        "emb": str(list(embeddings[i])),
                        "doc": documents[i],
                        "meta": json.dumps(metadatas[i]),
                    }
                    await session.execute(
                        text(f"""
                        INSERT INTO {self.collection_name} (id, embedding, document, metadata)
                        VALUES (:id, :emb, :doc, :meta)
                        ON CONFLICT (id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        document = EXCLUDED.document,
                        metadata = EXCLUDED.metadata
                    """),
                        params,
                    )
                await session.commit()
            print(f"📦 Added/updated {len(ids)} papers in PgVector")
        else:
            import asyncio

            batch_size = 100
            for i in range(0, len(ids), batch_size):
                await asyncio.to_thread(
                    self.collection.upsert,
                    ids=ids[i : i + batch_size],
                    embeddings=embeddings[i : i + batch_size],
                    documents=documents[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                )
            print(f"📦 Added/updated {len(ids)} papers in ChromaDB")

    async def search(
        self,
        query_embedding: list[float] | np.ndarray,
        top_k: int = 20,
        where: Optional[dict] = None,
    ) -> dict:
        """Search vectors appropriately and return strictly matching unified schema."""
        if not self._initialized:
            await self.initialize()

        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        start = time.time()

        if self.is_pg:
            params = {"emb": str(list(query_embedding)), "top_k": top_k}
            where_clause = ""
            if where:
                conds = []
                for k, v in where.items():
                    if isinstance(v, str):
                        conds.append(f"metadata->>'{k}' = :{k}")
                    else:
                        conds.append(f"(metadata->>'{k}')::numeric = :{k}")
                    params[k] = v
                where_clause = "WHERE " + " AND ".join(conds)

            async with async_session() as session:
                count_res = await session.execute(
                    text(f"SELECT COUNT(*) FROM {self.collection_name}")
                )
                if count_res.scalar() == 0:
                    return {
                        "ids": [[]],
                        "documents": [[]],
                        "distances": [[]],
                        "metadatas": [[]],
                    }

                res = await session.execute(
                    text(f"""
                    SELECT id, document, metadata, embedding <=> :emb AS distance
                    FROM {self.collection_name}
                    {where_clause}
                    ORDER BY embedding <=> :emb
                    LIMIT :top_k
                """),
                    params,
                )

                rows = res.fetchall()
                ids_res, doc_res, meta_res, dist_res = [], [], [], []
                for row in rows:
                    ids_res.append(row[0])
                    doc_res.append(row[1])
                    meta_res.append(
                        json.loads(row[2]) if isinstance(row[2], str) else row[2]
                    )
                    dist_res.append(float(row[3]))

                elapsed = time.time() - start
                print(
                    f"🔍 PgVector search: {len(ids_res)} results in {elapsed * 1000:.0f}ms"
                )
                return {
                    "ids": [ids_res],
                    "documents": [doc_res],
                    "distances": [dist_res],
                    "metadatas": [meta_res],
                }
        else:
            import asyncio

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

            results = await asyncio.to_thread(self.collection.query, **kwargs)
            elapsed = time.time() - start
            cnt = len(results["ids"][0]) if results["ids"] else 0
            print(f"🔍 ChromaDB search: {cnt} results in {elapsed * 1000:.0f}ms")
            return results

    async def delete(self, ids: list[str]):
        if not self._initialized:
            await self.initialize()
        if self.is_pg:
            async with async_session() as session:
                params = {"ids": ids}
                await session.execute(
                    text(f"DELETE FROM {self.collection_name} WHERE id = ANY(:ids)"),
                    params,
                )
                await session.commit()
        else:
            import asyncio

            await asyncio.to_thread(self.collection.delete, ids=ids)

    async def get_stats(self) -> dict:
        if not self._initialized:
            await self.initialize()
        c = await self.count()
        return {
            "total_vectors": c,
            "collection_name": self.collection_name,
            "backend": "pgvector" if self.is_pg else "chromadb",
        }

    async def count(self) -> int:
        if not self._initialized:
            await self.initialize()
        if self.is_pg:
            async with async_session() as session:
                res = await session.execute(
                    text(f"SELECT COUNT(*) FROM {self.collection_name}")
                )
                return res.scalar()
        else:
            import asyncio

            return await asyncio.to_thread(self.collection.count)


# Global singleton
vector_store = VectorStore()
