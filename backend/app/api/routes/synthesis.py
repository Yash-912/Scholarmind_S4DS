"""
Synthesis Routes — RAG-powered research synthesis endpoints.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.database import get_db
from app.llmops.synthesizer import synthesizer
from app.llmops.gateway import llm_gateway
from app.llmops.prompt_registry import prompt_registry
from app.llmops.cache import semantic_cache

router = APIRouter(prefix="/synthesis", tags=["Synthesis"])


@router.post("")
async def synthesize(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Run a full RAG synthesis pipeline.

    Body:
        query: Research question
        query_type: Optional override (synthesis, comparison, gap_analysis, chat)
        model: Optional model override
        top_k: Number of papers to retrieve (default: 15)
        use_cache: Whether to use semantic cache (default: true)
    """
    query = body.get("query", "")
    if not query:
        return {"error": "Query is required"}

    result = await synthesizer.synthesize(
        query=query,
        query_type=body.get("query_type"),
        model=body.get("model"),
        top_k=body.get("top_k"),
        use_cache=body.get("use_cache", True),
        check_hallucination=body.get("check_hallucination", True),
    )

    return result


@router.post("/stream")
async def synthesize_stream(body: dict):
    """
    Stream a synthesis response using SSE.
    """
    query = body.get("query", "")
    if not query:
        return {"error": "Query is required"}

    from app.core.retriever import retriever
    from app.core.reranker import reranker
    from app.config import settings

    # Retrieve and rerank
    retrieved = await retriever.retrieve(query=query, top_k=30)
    docs = [{"text": p.text, "title": p.title, "paper_id": p.paper_id} for p in retrieved]

    if settings.RERANKER_ENABLED:
        reranked = reranker.rerank(query, docs, top_k=settings.MAX_CONTEXT_CHUNKS)
    else:
        reranked = docs[:settings.MAX_CONTEXT_CHUNKS]

    papers_for_prompt = [{"title": d["title"], "text": d["text"][:800]} for d in reranked]
    prompt, system_prompt, _ = prompt_registry.render("synthesis", query=query, papers=papers_for_prompt)

    async def event_stream():
        async for chunk in llm_gateway.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
        ):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/prompts")
async def list_prompts():
    """List available prompt templates."""
    return {"prompts": prompt_registry.list_templates()}


@router.get("/cache/stats")
async def cache_stats():
    """Get semantic cache statistics."""
    return semantic_cache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear the semantic cache."""
    semantic_cache.clear()
    return {"message": "Cache cleared"}


@router.get("/models")
async def available_models():
    """List available LLM models."""
    return {"models": llm_gateway.get_available_models()}
