"""
PubMed API Scraper — Fetches real papers from PubMed E-utilities.
"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from app.ingestion.arxiv_scraper import RawPaper


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


async def scrape_pubmed(
    query: str = "machine learning healthcare",
    max_results: int = 50,
) -> list[RawPaper]:
    """
    Fetch papers from PubMed using E-utilities API.

    Args:
        query: PubMed search query
        max_results: Maximum number of results

    Returns:
        List of RawPaper objects
    """
    print(f"📡 Fetching from PubMed: query='{query}', max={max_results}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "sort": "date",
            "retmode": "xml",
        }
        search_resp = await client.get(PUBMED_ESEARCH_URL, params=search_params)
        search_resp.raise_for_status()

        # Parse PMIDs
        search_root = ET.fromstring(search_resp.text)
        pmids = [id_elem.text for id_elem in search_root.findall(".//Id") if id_elem.text]

        if not pmids:
            print("⚠️ No PubMed results found")
            return []

        # Step 2: Fetch full records
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        fetch_resp = await client.get(PUBMED_EFETCH_URL, params=fetch_params)
        fetch_resp.raise_for_status()

    # Parse articles
    root = ET.fromstring(fetch_resp.text)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        try:
            medline = article.find(".//MedlineCitation")
            if medline is None:
                continue

            pmid = medline.findtext(".//PMID", "")
            art = medline.find(".//Article")
            if art is None:
                continue

            # Title
            title = art.findtext(".//ArticleTitle", "").strip()
            if not title:
                continue

            # Abstract
            abstract_parts = []
            for abs_text in art.findall(".//Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = abs_text.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts).strip()

            if not abstract:
                continue

            # Authors
            authors = []
            for author in art.findall(".//AuthorList/Author"):
                last = author.findtext("LastName", "")
                first = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{first} {last}".strip())

            # Published date
            pub_date = art.find(".//Journal/JournalIssue/PubDate")
            published = None
            if pub_date is not None:
                year = pub_date.findtext("Year", "")
                month = pub_date.findtext("Month", "01")
                day = pub_date.findtext("Day", "01")
                try:
                    # Handle month names
                    month_map = {
                        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
                    }
                    if month in month_map:
                        month = month_map[month]
                    published = datetime(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    if year:
                        try:
                            published = datetime(int(year), 1, 1)
                        except ValueError:
                            pass

            # DOI
            doi = None
            for eid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                if eid.get("IdType") == "doi":
                    doi = eid.text

            # MeSH terms as categories
            mesh_terms = []
            for mesh in medline.findall(".//MeshHeadingList/MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            # Journal name
            journal = art.findtext(".//Journal/Title", "")

            paper = RawPaper(
                title=title,
                abstract=abstract,
                authors=authors,
                source="pubmed",
                source_id=f"PMID:{pmid}",
                doi=doi,
                published_date=published,
                categories=mesh_terms[:10],  # Limit to 10 MeSH terms
            )
            papers.append(paper)

        except Exception as e:
            print(f"⚠️ Error parsing PubMed article: {e}")
            continue

    print(f"✅ Fetched {len(papers)} papers from PubMed")
    return papers
