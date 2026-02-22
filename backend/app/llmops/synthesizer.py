"""
Synthesizer — The main RAG orchestrator.
Connects retrieval → re-ranking → LLM generation → hallucination checking.
"""

import time
from typing import Optional

from app.core.retriever import retriever
from app.core.reranker import reranker
from app.llmops.gateway import llm_gateway
from app.llmops.prompt_registry import prompt_registry
from app.llmops.cache import semantic_cache
from app.llmops.hallucination import hallucination_checker
from app.llmops.cost_tracker import cost_tracker
from app.db.database import async_session
from app.db import crud
from app.config import settings


class Synthesizer:
    """
    Full RAG synthesis pipeline:
    1. Query understanding
    2. Hybrid retrieval (dense + BM25)
    3. Cross-encoder re-ranking
    4. LLM synthesis with versioned prompts
    5. Hallucination checking
    6. Cost + quality logging
    """

    def _classify_query(self, query: str) -> str:
        """
        Classify query type based on keywords.
        Returns one of: synthesis, comparison, gap_analysis, summarize_single, chat
        """
        q = query.lower()

        if any(
            kw in q
            for kw in ["compare", "vs", "versus", "difference between", "contrast"]
        ):
            return "comparison"
        if any(
            kw in q
            for kw in ["gap", "missing", "unexplored", "not studied", "what hasn't"]
        ):
            return "gap_analysis"
        if any(
            kw in q
            for kw in ["summarize this paper", "summary of", "explain this paper"]
        ):
            return "summarize_single"
        if any(
            kw in q
            for kw in [
                "latest",
                "advances",
                "overview",
                "state of",
                "what are",
                "how has",
            ]
        ):
            return "synthesis"

        return "chat"

    async def synthesize(
        self,
        query: str,
        query_type: Optional[str] = None,
        model: Optional[str] = None,
        top_k: int = None,
        use_cache: bool = True,
        check_hallucination: bool = True,
    ) -> dict:
        """
        Full RAG synthesis pipeline.

        Args:
            query: User's research question
            query_type: Override auto-detected query type
            model: Override default LLM model
            top_k: Number of papers to retrieve
            use_cache: Whether to use semantic cache
            check_hallucination: Whether to run hallucination check

        Returns:
            dict with: answer, papers, query_type, metrics
        """
        start_time = time.time()
        top_k = top_k or settings.MAX_RETRIEVAL_RESULTS

        # Auto-classify query type and select model from router
        if not model or not query_type:
            from app.llmops.router import query_router
            decision = await query_router.route(query, query_type)
            model = model or decision.model
            query_type = query_type or "synthesis" # Default template
            
        from app.aiops.metrics_collector import queries_total
        queries_total.labels(query_type=query_type, cache_hit=str(False)).inc()

        # ═══ Step 1: Check Cache ═══
        if use_cache:
            cached = semantic_cache.get(query)
            if cached:
                # Log as cache hit
                async with async_session() as db:
                    await crud.log_query(
                        db,
                        query_text=query,
                        query_type=query_type,
                        cache_hit=True,
                        latency_ms=(time.time() - start_time) * 1000,
                    )
                    await db.commit()

                cached["cache_hit"] = True
                return cached

        # ═══ Step 2: Retrieve Papers ═══
        retrieved = await retriever.retrieve(
            query=query,
            top_k=top_k * 3,  # Over-retrieve for re-ranking
        )

        if not retrieved:
            return {
                "answer": "I couldn't find any relevant papers for your query. Try rephrasing or broadening your search.",
                "papers": [],
                "query_type": query_type,
                "metrics": {"latency_ms": (time.time() - start_time) * 1000},
                "cache_hit": False,
            }

        # ═══ Step 3: Re-rank ═══
        docs_for_rerank = [
            {
                "text": p.text,
                "paper_id": p.paper_id,
                "title": p.title,
                "score": p.score,
                "metadata": p.metadata,
            }
            for p in retrieved
        ]

        if settings.RERANKER_ENABLED:
            reranked = reranker.rerank(
                query, docs_for_rerank, top_k=settings.MAX_CONTEXT_CHUNKS
            )
        else:
            reranked = docs_for_rerank[: settings.MAX_CONTEXT_CHUNKS]

        # ═══ Step 4: Generate Synthesis ═══
        papers_for_prompt = [
            {"title": d["title"], "text": d["text"][:800]} for d in reranked
        ]

        prompt, system_prompt, prompt_version = prompt_registry.render(
            query_type,
            query=query,
            papers=papers_for_prompt,
        )

        llm_result = await llm_gateway.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
        )

        # Track cost
        cost_tracker.record(
            model=llm_result["model"],
            provider=llm_result["provider"],
            cost_usd=llm_result["cost_usd"],
            tokens=llm_result["input_tokens"] + llm_result["output_tokens"],
        )

        # ═══ Step 5: Hallucination Check ═══
        faithfulness_score = None
        hallucination_result = None

        if check_hallucination:
            hallucination_result = await hallucination_checker.check(
                generated_text=llm_result["text"],
                source_papers=papers_for_prompt,
            )
            faithfulness_score = hallucination_result.get("faithfulness_score")

        # ═══ Step 6: Build Response ═══
        total_latency = (time.time() - start_time) * 1000

        response = {
            "answer": llm_result["text"],
            "papers": [
                {
                    "paper_id": d.get("paper_id"),
                    "title": d.get("title", ""),
                    "score": d.get("rerank_score", d.get("score", 0)),
                    "source": d.get("metadata", {}).get("source", ""),
                }
                for d in reranked
            ],
            "query_type": query_type,
            "model": llm_result["model"],
            "prompt_version": prompt_version,
            "cache_hit": False,
            "metrics": {
                "latency_ms": round(total_latency, 2),
                "input_tokens": llm_result["input_tokens"],
                "output_tokens": llm_result["output_tokens"],
                "cost_usd": llm_result["cost_usd"],
                "papers_retrieved": len(retrieved),
                "papers_reranked": len(reranked),
                "faithfulness_score": faithfulness_score,
            },
        }

        if hallucination_result:
            response["hallucination_check"] = {
                "score": faithfulness_score,
                "flagged_claims": hallucination_result.get("flagged_claims", [])[:5],
            }

        # ═══ Step 7: Cache + Log ═══
        if use_cache:
            semantic_cache.put(query, response)

        async with async_session() as db:
            await crud.log_query(
                db,
                query_text=query,
                query_type=query_type,
                model_used=llm_result["model"],
                provider=llm_result["provider"],
                prompt_version=prompt_version,
                input_tokens=llm_result["input_tokens"],
                output_tokens=llm_result["output_tokens"],
                cost_usd=llm_result["cost_usd"],
                latency_ms=total_latency,
                cache_hit=False,
                faithfulness_score=faithfulness_score,
                num_papers_retrieved=len(reranked),
            )
            await db.commit()

        return response


# Global singleton
synthesizer = Synthesizer()
