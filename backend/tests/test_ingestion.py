"""Tests for the ingestion pipeline — verifies scrapers return real data."""

import pytest
from app.ingestion.arxiv_scraper import scrape_arxiv, RawPaper
from app.ingestion.pubmed_scraper import scrape_pubmed
from app.ingestion.parser import normalize_paper


@pytest.mark.asyncio
async def test_arxiv_scraper_returns_papers():
    papers = await scrape_arxiv(categories=["cs.AI"], max_results=5)
    assert len(papers) > 0
    assert isinstance(papers[0], RawPaper)
    assert papers[0].title
    assert papers[0].abstract


@pytest.mark.asyncio
async def test_pubmed_scraper_returns_papers():
    papers = await scrape_pubmed(query="deep learning healthcare", max_results=5)
    assert len(papers) > 0
    assert isinstance(papers[0], RawPaper)
    assert papers[0].title


def test_parser_normalizes_arxiv_paper():
    raw = RawPaper(
        title="Test Paper",
        abstract="This is a test abstract.",
        authors=["Author A"],
        source="arxiv",
        source_id="2401.00001",
    )
    parsed = normalize_paper(raw)
    assert parsed["title"] == "Test Paper"
    assert parsed["source"] == "arxiv"


def test_parser_skips_empty_title():
    raw = RawPaper(
        title="",
        abstract="Some abstract.",
        authors=[],
        source="arxiv",
        source_id="2401.00002",
    )
    parsed = normalize_paper(raw)
    assert parsed is None


def test_parser_cleans_abstract():
    raw = RawPaper(
        title="Test Paper",
        abstract="",
        authors=["Author A"],
        source="pubmed",
        source_id="PMID:123",
    )
    parsed = normalize_paper(raw)
    assert parsed["abstract"] == "No abstract available."
