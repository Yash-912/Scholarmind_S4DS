"""
arXiv API Scraper — Fetches real papers from arXiv.
Uses the arXiv API (Atom feed) with feedparser.
"""

import feedparser
import httpx
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


ARXIV_API_URL = "https://export.arxiv.org/api/query"


@dataclass
class RawPaper:
    """Raw paper data from a scraper source."""
    title: str
    abstract: str
    authors: list[str]
    source: str
    source_id: str
    doi: Optional[str] = None
    published_date: Optional[datetime] = None
    categories: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    citation_count: int = 0
    pdf_url: Optional[str] = None


async def scrape_arxiv(
    categories: list[str],
    max_results: int = 100,
    start: int = 0,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
) -> list[RawPaper]:
    """
    Fetch papers from arXiv API.

    Args:
        categories: List of arXiv categories (e.g., ["cs.AI", "cs.LG"])
        max_results: Maximum number of results to return
        start: Starting index for pagination
        sort_by: Sort field ("relevance", "lastUpdatedDate", "submittedDate")
        sort_order: Sort order ("ascending", "descending")

    Returns:
        List of RawPaper objects
    """
    # Build category query: cat:cs.AI OR cat:cs.LG OR ...
    cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
    search_query = f"({cat_query})"

    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }

    print(f"📡 Fetching from arXiv: {categories}, max_results={max_results}")

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(ARXIV_API_URL, params=params)
        response.raise_for_status()

    # Parse Atom feed
    feed = feedparser.parse(response.text)
    papers = []

    for entry in feed.entries:
        try:
            # Extract arXiv ID
            arxiv_id = entry.id.split("/abs/")[-1]

            # Extract authors
            authors = [author.get("name", "") for author in entry.get("authors", [])]

            # Extract categories
            categories_list = [tag["term"] for tag in entry.get("tags", [])]

            # Extract DOI if available
            doi = None
            for link in entry.get("links", []):
                if link.get("title") == "doi":
                    doi = link.get("href", "").replace("http://dx.doi.org/", "")

            # Extract PDF URL
            pdf_url = None
            for link in entry.get("links", []):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break

            # Parse published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            # Clean abstract (remove newlines and extra whitespace)
            abstract = entry.get("summary", "").replace("\n", " ").strip()
            title = entry.get("title", "").replace("\n", " ").strip()

            paper = RawPaper(
                title=title,
                abstract=abstract,
                authors=authors,
                source="arxiv",
                source_id=arxiv_id,
                doi=doi,
                published_date=published,
                categories=categories_list,
                pdf_url=pdf_url,
            )
            papers.append(paper)

        except Exception as e:
            print(f"⚠️ Error parsing arXiv entry: {e}")
            continue

    print(f"✅ Fetched {len(papers)} papers from arXiv")
    return papers


async def scrape_arxiv_by_query(
    query: str,
    max_results: int = 50,
) -> list[RawPaper]:
    """
    Fetch papers from arXiv by search query.

    Args:
        query: Search query string
        max_results: Maximum results

    Returns:
        List of RawPaper objects
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(ARXIV_API_URL, params=params)
        response.raise_for_status()

    feed = feedparser.parse(response.text)
    papers = []

    for entry in feed.entries:
        try:
            arxiv_id = entry.id.split("/abs/")[-1]
            authors = [a.get("name", "") for a in entry.get("authors", [])]
            categories_list = [tag["term"] for tag in entry.get("tags", [])]
            abstract = entry.get("summary", "").replace("\n", " ").strip()
            title = entry.get("title", "").replace("\n", " ").strip()

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            pdf_url = None
            for link in entry.get("links", []):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break

            papers.append(RawPaper(
                title=title,
                abstract=abstract,
                authors=authors,
                source="arxiv",
                source_id=arxiv_id,
                published_date=published,
                categories=categories_list,
                pdf_url=pdf_url,
            ))
        except Exception as e:
            print(f"⚠️ Error parsing: {e}")
            continue

    return papers
