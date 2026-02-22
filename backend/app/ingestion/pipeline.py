"""
Ingestion Pipeline — Orchestrates the full scrape → dedup → embed → store flow.
"""

import time
import asyncio

from app.ingestion.arxiv_scraper import scrape_arxiv, RawPaper
from app.ingestion.pubmed_scraper import scrape_pubmed
from app.ingestion.semantic_scholar import enrich_from_semantic_scholar
from app.ingestion.parser import normalize_paper
from app.ingestion.dedup import is_duplicate
from app.core.embeddings import embedding_service
from app.core.vector_store import vector_store
from app.db.database import async_session
from app.db import crud
from app.config import settings


async def run_ingestion_pipeline(
    sources: list[str] = None,
    max_arxiv: int = None,
    max_pubmed: int = None,
) -> dict:
    """
    Run the full ingestion pipeline.

    Args:
        sources: List of sources to scrape (default: ["arxiv", "pubmed"])
        max_arxiv: Override max arXiv results
        max_pubmed: Override max PubMed results

    Returns:
        Dict with pipeline run statistics
    """
    if sources is None:
        sources = ["arxiv", "pubmed"]

    max_arxiv = max_arxiv or settings.ARXIV_MAX_RESULTS
    max_pubmed = max_pubmed or settings.PUBMED_MAX_RESULTS

    start_time = time.time()
    stats = {
        "papers_found": 0,
        "papers_new": 0,
        "papers_duplicate": 0,
        "papers_failed": 0,
        "papers_enriched": 0,
        "source": ",".join(sources),
    }

    # Track the ingestion run in DB
    async with async_session() as db:
        run = await crud.create_ingestion_run(
            db,
            source=stats["source"],
            status="running",
        )
        run_id = run.id
        await db.commit()

    print(f"\n{'=' * 60}")
    print(f"🚀 INGESTION PIPELINE STARTED — Sources: {sources}")
    print(f"{'=' * 60}\n")

    # ═══ Step 1: Scrape Papers ═══
    raw_papers: list[RawPaper] = []

    if "arxiv" in sources:
        try:
            arxiv_papers = await scrape_arxiv(
                categories=settings.arxiv_categories_list,
                max_results=max_arxiv,
            )
            raw_papers.extend(arxiv_papers)
        except Exception as e:
            print(f"❌ arXiv scraping failed: {e}")

    if "pubmed" in sources:
        try:
            pubmed_papers = await scrape_pubmed(
                query=settings.PUBMED_QUERY,
                max_results=max_pubmed,
            )
            raw_papers.extend(pubmed_papers)
        except Exception as e:
            print(f"❌ PubMed scraping failed: {e}")

    stats["papers_found"] = len(raw_papers)
    print(f"\n📊 Total papers found: {stats['papers_found']}")

    if not raw_papers:
        print("⚠️ No papers to process")
        async with async_session() as db:
            await crud.complete_ingestion_run(
                db,
                run_id,
                status="completed",
                **stats,
                duration_seconds=time.time() - start_time,
            )
            await db.commit()
        return stats

    # ═══ Step 2: Dedup + Parse + Store in DB ═══
    new_papers = []

    async with async_session() as db:
        for raw in raw_papers:
            try:
                # Parse
                parsed = normalize_paper(raw)
                if parsed is None:
                    stats["papers_failed"] += 1
                    continue

                # Dedup
                is_dup, existing_id = await is_duplicate(
                    db,
                    source_id=parsed["source_id"],
                    doi=parsed.get("doi"),
                    title=parsed["title"],
                )

                if is_dup:
                    stats["papers_duplicate"] += 1
                    continue

                # Store in DB
                paper = await crud.create_paper(db, **parsed)
                new_papers.append((paper, parsed))
                stats["papers_new"] += 1

            except Exception as e:
                stats["papers_failed"] += 1
                print(f"⚠️ Failed to process paper: {e}")
                continue

        await db.commit()

    print(
        f"\n📊 New papers: {stats['papers_new']}, Duplicates: {stats['papers_duplicate']}, Failed: {stats['papers_failed']}"
    )

    # ═══ Step 3: Generate Embeddings ═══
    if new_papers:
        print(f"\n🔄 Generating embeddings for {len(new_papers)} papers...")

        # Prepare texts for embedding
        texts = [
            embedding_service.format_paper_text(p["title"], p["abstract"])
            for _, p in new_papers
        ]

        # Generate embeddings
        embeddings = embedding_service.embed_texts(texts)

        # ═══ Step 4: Store in Vector DB ═══
        ids = [str(paper.id) for paper, _ in new_papers]
        documents = texts
        metadatas = [
            {
                "paper_id": paper.id,
                "source": p["source"],
                "source_id": p["source_id"],
                "title": p["title"][:500],
                "published_date": p["published_date"].isoformat()
                if p["published_date"]
                else "",
                "categories": ",".join(p["categories"][:5]),
            }
            for paper, p in new_papers
        ]

        await vector_store.add_papers(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        # Update embedding_id in DB
        async with async_session() as db:
            for (paper, _), emb_id in zip(new_papers, ids):
                db_paper = await crud.get_paper(db, paper.id)
                if db_paper:
                    db_paper.embedding_id = emb_id
            await db.commit()

    # ═══ Step 5: Enrich with Semantic Scholar (async, limited) ═══
    enrichment_count = 0
    for paper, parsed in new_papers[:20]:  # Limit to 20 to avoid rate limits
        try:
            enrichment = await enrich_from_semantic_scholar(
                doi=parsed.get("doi"),
                arxiv_id=parsed["source_id"] if parsed["source"] == "arxiv" else None,
            )
            if enrichment:
                async with async_session() as db:
                    db_paper = await crud.get_paper(db, paper.id)
                    if db_paper:
                        db_paper.citation_count = enrichment.citation_count
                        if enrichment.references:
                            db_paper.references = enrichment.references
                    await db.commit()
                enrichment_count += 1

            # Rate limit: 1 request per second for S2 API
            await asyncio.sleep(1.0)

        except Exception as e:
            print(f"⚠️ S2 enrichment failed: {e}")
            continue

    stats["papers_enriched"] = enrichment_count

    # ═══ Step 6: Complete Run ═══
    duration = time.time() - start_time
    stats["duration_seconds"] = round(duration, 2)

    async with async_session() as db:
        await crud.complete_ingestion_run(
            db,
            run_id,
            status="completed",
            papers_found=stats["papers_found"],
            papers_new=stats["papers_new"],
            papers_duplicate=stats["papers_duplicate"],
            papers_failed=stats["papers_failed"],
            duration_seconds=duration,
        )
        await db.commit()

    print(f"\n{'=' * 60}")
    print(f"✅ PIPELINE COMPLETE in {duration:.1f}s")
    print(
        f"   Found: {stats['papers_found']} | New: {stats['papers_new']} | Dupes: {stats['papers_duplicate']} | Failed: {stats['papers_failed']}"
    )
    vc = await vector_store.count()
    print(f"   Enriched: {stats['papers_enriched']} | Vectors: {vc}")
    print(f"{'=' * 60}\n")

    return stats
