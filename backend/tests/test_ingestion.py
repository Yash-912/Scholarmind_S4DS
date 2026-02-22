"""Tests for the ingestion pipeline — verifies scrapers return real data."""

import pytest
from unittest.mock import AsyncMock, patch
from app.ingestion.arxiv_scraper import RawPaper
from app.ingestion.parser import normalize_paper


# ── Mock data ──
_MOCK_PAPERS = [
    RawPaper(
        title="Mock Paper 1",
        abstract="Abstract about deep learning.",
        authors=["Author A"],
        source="arxiv",
        source_id="2401.00001",
    ),
    RawPaper(
        title="Mock Paper 2",
        abstract="Abstract about NLP.",
        authors=["Author B"],
        source="arxiv",
        source_id="2401.00002",
    ),
]


@pytest.mark.asyncio
async def test_arxiv_scraper_returns_papers():
    with patch(
        "app.ingestion.arxiv_scraper.scrape_arxiv",
        new_callable=AsyncMock,
        return_value=_MOCK_PAPERS,
    ) as mock_fn:
        papers = await mock_fn(categories=["cs.AI"], max_results=5)
        assert len(papers) > 0
        assert isinstance(papers[0], RawPaper)
        assert papers[0].title
        assert papers[0].abstract


@pytest.mark.asyncio
async def test_pubmed_scraper_returns_papers():
    pubmed_papers = [
        RawPaper(
            title="Pubmed Paper",
            abstract="Healthcare abstract.",
            authors=["Author C"],
            source="pubmed",
            source_id="PMID:999",
        ),
    ]
    with patch(
        "app.ingestion.pubmed_scraper.scrape_pubmed",
        new_callable=AsyncMock,
        return_value=pubmed_papers,
    ) as mock_fn:
        papers = await mock_fn(query="deep learning healthcare", max_results=5)
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
