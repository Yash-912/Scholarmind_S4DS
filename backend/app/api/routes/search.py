"""
Search Routes — Semantic search over papers.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.retriever import retriever
from app.core.reranker import reranker
from app.config import settings

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def semantic_search(
    q: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(20, ge=1, le=100),
    use_reranker: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Hybrid semantic search over papers.
    Uses dense + sparse retrieval with optional re-ranking.
    """
    # Retrieve
    results = await retriever.retrieve(
        query=q, top_k=top_k * 2 if use_reranker else top_k
    )

    # Re-rank if enabled
    if use_reranker and settings.RERANKER_ENABLED and results:
        docs = [
            {
                "text": p.text,
                "paper_id": p.paper_id,
                "title": p.title,
                "score": p.score,
                "metadata": p.metadata,
            }
            for p in results
        ]
        reranked = reranker.rerank(q, docs, top_k=top_k)
        return {
            "query": q,
            "results": [
                {
                    "paper_id": d["paper_id"],
                    "title": d["title"],
                    "score": round(d.get("rerank_score", d.get("score", 0)), 4),
                    "source": d.get("metadata", {}).get("source", ""),
                    "snippet": d["text"][:300] + "..."
                    if len(d["text"]) > 300
                    else d["text"],
                }
                for d in reranked
            ],
            "count": len(reranked),
            "reranked": True,
        }

    return {
        "query": q,
        "results": [
            {
                "paper_id": p.paper_id,
                "title": p.title,
                "score": round(p.score, 4),
                "source": p.source,
                "snippet": p.text[:300] + "..." if len(p.text) > 300 else p.text,
            }
            for p in results[:top_k]
        ],
        "count": min(len(results), top_k),
        "reranked": False,
    }
