"""
Semantic Scholar Search Helper

Provides functions to search Semantic Scholar for academic papers.
No API key required for basic usage (100 requests/5 minutes).
With API key: higher rate limits.

Usage:
    from skills.semantic_scholar import search_papers, get_paper

    papers = search_papers("transformer attention mechanism", max_results=20)
"""

import urllib.request
import urllib.parse
import json
import ssl
import time
from typing import Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SEMANTIC_SCHOLAR_BASE_URL, SEMANTIC_SCHOLAR_API_KEY, DEFAULT_MAX_RESULTS


def _create_unverified_ssl_context():
    """Create unverified SSL context for systems with certificate issues."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


_SSL_CONTEXT = _create_unverified_ssl_context()


def _build_headers() -> dict:
    """Build request headers with optional API key."""
    headers = {"Accept": "application/json"}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    return headers


# Rate limiting: conservative for 100 req/5 min without key
_last_request_time = 0.0


def _rate_limit():
    """Ensure we don't exceed rate limits."""
    global _last_request_time
    interval = 1.0 if SEMANTIC_SCHOLAR_API_KEY else 3.0
    elapsed = time.time() - _last_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_time = time.time()


def _make_request(url: str, retry_on_429: bool = True) -> Optional[dict]:
    """Make a request to Semantic Scholar API with retry on 429."""
    headers = _build_headers()
    request = urllib.request.Request(url, headers=headers)

    for attempt in range(2):
        try:
            _rate_limit()
            with urllib.request.urlopen(request, timeout=30, context=_SSL_CONTEXT) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0 and retry_on_429:
                print("[WARNING] Semantic Scholar rate limited, retrying in 4s...", file=sys.stderr)
                time.sleep(4)
                continue
            print(f"[ERROR] Semantic Scholar HTTP {e.code}: {e.reason}", file=sys.stderr)
            return None
        except Exception as e:
            if attempt == 0:
                print(f"[WARNING] Semantic Scholar request failed, retrying: {e}", file=sys.stderr)
                time.sleep(3)
                continue
            print(f"[ERROR] Semantic Scholar request failed: {e}", file=sys.stderr)
            return None

    return None


def search_papers(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fields: str = "title,authors,year,abstract,url,citationCount,externalIds,venue"
) -> list[dict]:
    """
    Search Semantic Scholar for academic papers.

    Args:
        query: Search query string
        max_results: Maximum number of results (max 100)
        year_from: Filter by publication year (start)
        year_to: Filter by publication year (end)
        fields: Comma-separated fields to return

    Returns:
        List of paper dictionaries with keys:
        - paper_id: Semantic Scholar paper ID
        - title: Paper title
        - authors: List of author names
        - year: Publication year
        - abstract: Abstract text
        - doi: DOI (if available)
        - arxiv_id: arXiv ID (if available)
        - venue: Publication venue
        - cited_by_count: Citation count
        - url: URL to the paper
        - source: "semantic_scholar"
    """
    if not query:
        return []

    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": fields,
    }

    if year_from and year_to:
        params["year"] = f"{year_from}-{year_to}"
    elif year_from:
        params["year"] = f"{year_from}-"
    elif year_to:
        params["year"] = f"-{year_to}"

    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/search?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if not data:
        return []

    papers = []
    for p in data.get("data", []):
        ext_ids = p.get("externalIds") or {}
        authors = [a.get("name", "") for a in p.get("authors", []) if a.get("name")]

        papers.append({
            "paper_id": p.get("paperId", ""),
            "title": p.get("title", ""),
            "authors": authors,
            "year": p.get("year"),
            "abstract": p.get("abstract") or "",
            "doi": ext_ids.get("DOI", ""),
            "arxiv_id": ext_ids.get("ArXiv", ""),
            "venue": p.get("venue") or "",
            "cited_by_count": p.get("citationCount") or 0,
            "url": p.get("url") or "",
            "source": "semantic_scholar",
        })

    return papers


def get_paper(paper_id: str) -> Optional[dict]:
    """
    Get details for a specific paper by Semantic Scholar ID or DOI.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID (prefixed with "ArXiv:")

    Returns:
        Paper dictionary or None if not found
    """
    fields = "title,authors,year,abstract,url,citationCount,externalIds,venue"
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/{urllib.parse.quote(paper_id, safe='')}?fields={fields}"

    data = _make_request(url, retry_on_429=True)
    if not data:
        return None

    ext_ids = data.get("externalIds") or {}
    authors = [a.get("name", "") for a in data.get("authors", []) if a.get("name")]

    return {
        "paper_id": data.get("paperId", ""),
        "title": data.get("title", ""),
        "authors": authors,
        "year": data.get("year"),
        "abstract": data.get("abstract") or "",
        "doi": ext_ids.get("DOI", ""),
        "arxiv_id": ext_ids.get("ArXiv", ""),
        "venue": data.get("venue") or "",
        "cited_by_count": data.get("citationCount") or 0,
        "url": data.get("url") or "",
        "source": "semantic_scholar",
    }


def format_citation(paper: dict) -> str:
    """Format a paper dictionary as a citation string."""
    authors = paper.get("authors", [])
    if len(authors) > 3:
        author_str = f"{authors[0]} et al."
    elif authors:
        author_str = ", ".join(authors)
    else:
        author_str = "Unknown"

    title = paper.get("title", "No title")
    venue = paper.get("venue", "")
    year = paper.get("year", "")

    citation = f"{author_str}. {title}."
    if venue:
        citation += f" {venue}."
    if year:
        citation += f" {year}."

    return citation


# Command-line interface for testing
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python semantic_scholar.py <search query>")
        print("Example: python semantic_scholar.py 'attention is all you need'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching Semantic Scholar for: {query}\n")

    papers = search_papers(query, max_results=5)

    if not papers:
        print(f'No results found for: "{query}"')
    else:
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            print(f"   {format_citation(paper)}")
            print(f"   Citations: {paper['cited_by_count']}")
            if paper["doi"]:
                print(f"   DOI: {paper['doi']}")
            if paper["arxiv_id"]:
                print(f"   arXiv: {paper['arxiv_id']}")
            print()
