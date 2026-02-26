"""
DBLP Search Helper

Provides functions to search DBLP for computer science publications.
No API key required. Free public API.

Note: DBLP does NOT provide abstracts or citation counts.
Use it for discovering CS publications, then look up details in Semantic Scholar or Crossref.

Usage:
    from skills.dblp import search_dblp

    papers = search_dblp("graph neural networks", max_results=20)
"""

import http.client
import urllib.parse
import json
import time
from typing import Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DBLP_BASE_URL, DEFAULT_MAX_RESULTS

# Rate limiting: 1 request per second (polite to DBLP)
# Initialize to current time so the first request gets a proper delay
_last_request_time = time.time()


def _rate_limit():
    """Ensure we don't exceed rate limits."""
    global _last_request_time
    interval = 1.0
    elapsed = time.time() - _last_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_time = time.time()


def _make_request(url: str) -> Optional[dict]:
    """Make a request to DBLP API using http.client.

    DBLP's server returns HTTP 500 with urllib.request.urlopen due to
    header/protocol negotiation differences. Using http.client directly works.
    Includes retry with backoff for transient 500 errors.
    """
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    if parsed.query:
        path += "?" + parsed.query

    for attempt in range(3):
        try:
            _rate_limit()
            conn = http.client.HTTPSConnection(parsed.hostname, timeout=30)
            conn.request("GET", path, headers={"User-Agent": "Mozilla/5.0"})
            resp = conn.getresponse()

            if resp.status == 429:
                print("[WARNING] DBLP rate limited", file=sys.stderr)
                resp.read()
                conn.close()
                return None

            if resp.status == 500 and attempt < 2:
                resp.read()
                conn.close()
                time.sleep(2 ** attempt)
                continue

            if resp.status != 200:
                print(f"[ERROR] DBLP HTTP {resp.status}: {resp.reason}", file=sys.stderr)
                resp.read()
                conn.close()
                return None

            data = json.loads(resp.read().decode())
            conn.close()
            return data

        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            print(f"[ERROR] DBLP request failed: {e}", file=sys.stderr)
            return None

    return None


# Stop words for query simplification
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to",
    "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "using", "based", "via", "between", "through", "into", "about",
    "how", "what", "which", "their", "its", "can", "do", "does",
}


def _simplify_query(query: str, max_terms: int = 3) -> str:
    """
    Simplify a query for DBLP which works best with short, keyword-style queries.

    DBLP search requires ALL terms to appear in titles, so long queries
    return 0 results. We keep only the most significant words.
    """
    words = query.replace("-", " ").split()
    significant = [w for w in words if w.lower() not in _STOP_WORDS and len(w) > 2]
    if len(significant) > max_terms:
        significant = significant[:max_terms]
    return " ".join(significant) if significant else query


def _transform_hit(info: dict) -> Optional[dict]:
    """Transform a DBLP hit into a standardized dictionary."""
    title = info.get("title", "")
    if not title:
        return None
    # DBLP titles sometimes end with a period
    title = title.rstrip(".")

    # Authors — DBLP returns either a string, list, or dict
    authors_raw = info.get("authors", {}).get("author", [])
    if isinstance(authors_raw, str):
        authors_raw = [authors_raw]
    elif isinstance(authors_raw, dict):
        # Single author as dict with "text" key
        authors_raw = [authors_raw.get("text", "")]

    authors = []
    for a in authors_raw[:10]:
        if isinstance(a, dict):
            name = a.get("text", "")
        else:
            name = str(a)
        if name:
            authors.append(name)

    # Year
    year = None
    try:
        year = int(info.get("year", 0))
    except (ValueError, TypeError):
        pass

    # DOI
    doi = info.get("doi", "")

    # Venue
    venue = info.get("venue", "")

    # URL — ee field can be string or list
    url = info.get("ee", "") or info.get("url", "")
    if isinstance(url, list):
        url = url[0] if url else ""

    return {
        "dblp_key": info.get("key", ""),
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": "",  # DBLP does not provide abstracts
        "doi": doi,
        "venue": venue,
        "url": url or (f"https://doi.org/{doi}" if doi else ""),
        "source": "dblp",
    }


def _fetch(search_query: str, max_results: int, year_from: Optional[int] = None, year_to: Optional[int] = None) -> list[dict]:
    """Execute a single DBLP search and return parsed papers."""
    params = {
        "q": search_query,
        "h": min(max_results, 40),
        "format": "json",
    }

    url = f"{DBLP_BASE_URL}?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if not data:
        return []

    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    papers = []
    for hit in hits:
        info = hit.get("info", {})
        paper = _transform_hit(info)
        if paper:
            # Year filter (applied post-fetch)
            if year_from or year_to:
                y = paper.get("year")
                if y is not None:
                    if year_from and y < year_from:
                        continue
                    if year_to and y > year_to:
                        continue
            papers.append(paper)

    return papers


def search_dblp(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> list[dict]:
    """
    Search DBLP for computer science publications.

    DBLP requires ALL terms to appear in titles, so long queries return 0.
    We simplify to 3 terms, and if that returns 0, fall back to 2 terms.

    Note: DBLP does NOT provide abstracts or citation counts.

    Args:
        query: Search query string
        max_results: Maximum number of results (max 40)
        year_from: Filter by publication year (start)
        year_to: Filter by publication year (end)

    Returns:
        List of paper dictionaries with keys:
        - dblp_key: DBLP key
        - title: Paper title
        - authors: List of author names
        - year: Publication year
        - abstract: Always empty string (DBLP limitation)
        - doi: DOI (if available)
        - venue: Publication venue
        - url: URL to the paper
        - source: "dblp"
    """
    if not query:
        return []

    # Try with 3 key terms
    simplified = _simplify_query(query, max_terms=3)
    papers = _fetch(simplified, max_results, year_from, year_to)

    # If 0 results and we had 3+ terms, retry with just 2
    if not papers and len(simplified.split()) >= 3:
        shorter = _simplify_query(query, max_terms=2)
        if shorter != simplified:
            papers = _fetch(shorter, max_results, year_from, year_to)

    return papers


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
        print("Usage: python dblp.py <search query>")
        print("Example: python dblp.py 'graph neural networks'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching DBLP for: {query}\n")

    papers = search_dblp(query, max_results=5)

    if not papers:
        print(f'No results found for: "{query}"')
    else:
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            print(f"   {format_citation(paper)}")
            if paper["doi"]:
                print(f"   DOI: {paper['doi']}")
            print(f"   URL: {paper['url']}")
            print()
