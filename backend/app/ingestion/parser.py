"""
Parser — Normalize raw scraper data into unified paper schema.
"""

from app.ingestion.arxiv_scraper import RawPaper


def normalize_paper(raw: RawPaper) -> dict:
    """
    Convert a RawPaper into a dict suitable for database insertion.
    Handles missing fields, cleans text, and standardizes format.

    Returns:
        Dict with keys matching Paper model columns.
    """
    # Clean and validate title
    title = raw.title.strip()
    if not title:
        return None

    # Clean abstract
    abstract = raw.abstract.strip()
    if not abstract:
        abstract = "No abstract available."

    # Normalize authors
    authors = raw.authors or []
    authors = [a.strip() for a in authors if a.strip()]

    # Normalize categories
    categories = raw.categories or []
    categories = [c.strip() for c in categories if c.strip()]

    return {
        "title": title[:1000],  # Truncate very long titles
        "abstract": abstract,
        "authors": authors,
        "source": raw.source,
        "source_id": raw.source_id,
        "doi": raw.doi,
        "published_date": raw.published_date,
        "categories": categories,
        "references": raw.references or [],
        "citation_count": raw.citation_count or 0,
        "pdf_url": raw.pdf_url,
    }
