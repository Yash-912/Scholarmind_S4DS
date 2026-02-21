"""
Semantic Scholar API — Enrich papers with citation data.
"""

import httpx
from typing import Optional
from dataclasses import dataclass


S2_API_URL = "https://api.semanticscholar.org/graph/v1"


@dataclass
class S2Enrichment:
    """Enrichment data from Semantic Scholar."""

    citation_count: int = 0
    influential_citation_count: int = 0
    references: list[str] = None  # list of reference paper IDs
    tldr: Optional[str] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []


async def enrich_from_semantic_scholar(
    doi: Optional[str] = None,
    arxiv_id: Optional[str] = None,
    title: Optional[str] = None,
) -> Optional[S2Enrichment]:
    """
    Enrich a paper with Semantic Scholar data.

    Args:
        doi: Paper DOI
        arxiv_id: arXiv ID
        title: Paper title (fallback search)

    Returns:
        S2Enrichment or None if not found
    """
    paper_id = None
    if doi:
        paper_id = f"DOI:{doi}"
    elif arxiv_id:
        paper_id = f"ARXIV:{arxiv_id}"

    if not paper_id and title:
        # Search by title
        return await _search_by_title(title)

    if not paper_id:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{S2_API_URL}/paper/{paper_id}"
            params = {
                "fields": "citationCount,influentialCitationCount,references.paperId,tldr"
            }
            response = await client.get(url, params=params)

            if response.status_code == 404:
                return None
            if response.status_code == 429:
                print("⚠️ Semantic Scholar rate limited")
                return None
            response.raise_for_status()

            data = response.json()
            refs = [
                r["paperId"] for r in data.get("references", []) if r.get("paperId")
            ]

            tldr_text = None
            if data.get("tldr"):
                tldr_text = data["tldr"].get("text")

            return S2Enrichment(
                citation_count=data.get("citationCount", 0),
                influential_citation_count=data.get("influentialCitationCount", 0),
                references=refs[:50],  # Limit to 50 references
                tldr=tldr_text,
            )

    except httpx.HTTPError as e:
        print(f"⚠️ Semantic Scholar API error: {e}")
        return None


async def _search_by_title(title: str) -> Optional[S2Enrichment]:
    """Search Semantic Scholar by title and return enrichment."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{S2_API_URL}/paper/search"
            params = {
                "query": title[:200],
                "limit": 1,
                "fields": "citationCount,influentialCitationCount,tldr",
            }
            response = await client.get(url, params=params)

            if response.status_code != 200:
                return None

            data = response.json()
            papers = data.get("data", [])
            if not papers:
                return None

            paper = papers[0]
            tldr_text = None
            if paper.get("tldr"):
                tldr_text = paper["tldr"].get("text")

            return S2Enrichment(
                citation_count=paper.get("citationCount", 0),
                influential_citation_count=paper.get("influentialCitationCount", 0),
                tldr=tldr_text,
            )

    except httpx.HTTPError:
        return None
