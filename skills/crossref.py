"""
Crossref Search Helper

Provides functions to search Crossref for DOI-registered scholarly works.
No API key required. Polite pool available with email in User-Agent.

Usage:
    from skills.crossref import search_crossref, get_work

    works = search_crossref("machine learning drug discovery", max_results=20)
"""

import urllib.request
import urllib.parse
import json
import ssl
import time
import re
from typing import Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CROSSREF_BASE_URL, CROSSREF_EMAIL, DEFAULT_MAX_RESULTS


def _create_unverified_ssl_context():
    """Create unverified SSL context for systems with certificate issues."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


_SSL_CONTEXT = _create_unverified_ssl_context()


def _build_headers() -> dict:
    """Build request headers with polite pool email if configured."""
    headers = {"Accept": "application/json"}
    if CROSSREF_EMAIL:
        headers["User-Agent"] = f"ResearchEngine/1.0 (mailto:{CROSSREF_EMAIL})"
    else:
        headers["User-Agent"] = "ResearchEngine/1.0"
    return headers


# Rate limiting: polite pool
_last_request_time = 0.0


def _rate_limit():
    """Ensure we don't exceed rate limits."""
    global _last_request_time
    interval = 0.5  # polite interval
    elapsed = time.time() - _last_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_time = time.time()


def _make_request(url: str) -> Optional[dict]:
    """Make a request to Crossref API with retry on 429."""
    headers = _build_headers()
    request = urllib.request.Request(url, headers=headers)

    for attempt in range(2):
        try:
            _rate_limit()
            with urllib.request.urlopen(request, timeout=30, context=_SSL_CONTEXT) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                print("[WARNING] Crossref rate limited, retrying in 3s...", file=sys.stderr)
                time.sleep(3)
                continue
            print(f"[ERROR] Crossref HTTP {e.code}: {e.reason}", file=sys.stderr)
            return None
        except Exception as e:
            if attempt == 0:
                print(f"[WARNING] Crossref request failed, retrying: {e}", file=sys.stderr)
                time.sleep(2)
                continue
            print(f"[ERROR] Crossref request failed: {e}", file=sys.stderr)
            return None

    return None


def _transform_work(item: dict) -> Optional[dict]:
    """Transform a Crossref work item into a standardized dictionary."""
    # Title (Crossref wraps titles in arrays)
    titles = item.get("title", [])
    title = titles[0] if titles else None
    if not title:
        return None

    # Authors
    authors = []
    for author in item.get("author", [])[:10]:
        given = author.get("given", "")
        family = author.get("family", "")
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)

    # DOI
    doi = item.get("DOI", "")

    # Year from published-print or published-online
    year = None
    for date_field in ["published-print", "published-online"]:
        date_parts = item.get(date_field, {}).get("date-parts", [[]])
        if date_parts and date_parts[0] and date_parts[0][0]:
            year = date_parts[0][0]
            break

    # Venue/journal
    containers = item.get("container-title", [])
    journal = containers[0] if containers else ""

    # Abstract (Crossref returns XML-tagged abstracts)
    abstract = item.get("abstract", "")
    if abstract:
        abstract = re.sub(r'<[^>]+>', '', abstract).strip()

    return {
        "doi": doi,
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "journal": journal,
        "cited_by_count": item.get("is-referenced-by-count", 0),
        "url": item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
        "type": item.get("type", ""),
        "source": "crossref",
    }


def search_crossref(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> list[dict]:
    """
    Search Crossref for DOI-registered scholarly works.

    Args:
        query: Search query string
        max_results: Maximum number of results (max 50)
        year_from: Filter by publication year (start)
        year_to: Filter by publication year (end)

    Returns:
        List of work dictionaries with keys:
        - doi: DOI
        - title: Work title
        - authors: List of author names
        - year: Publication year
        - abstract: Abstract (if available, XML tags stripped)
        - journal: Journal/container title
        - cited_by_count: Citation count
        - url: URL to the work
        - type: Work type (journal-article, etc.)
        - source: "crossref"
    """
    if not query:
        return []

    params = {
        "query": query,
        "rows": min(max_results, 50),
        "sort": "relevance",
        "order": "desc",
        "select": "DOI,title,author,published-print,published-online,container-title,is-referenced-by-count,abstract,type,URL",
    }

    # Year filter
    if year_from or year_to:
        filters = []
        if year_from:
            filters.append(f"from-pub-date:{year_from}")
        if year_to:
            filters.append(f"until-pub-date:{year_to}")
        params["filter"] = ",".join(filters)

    url = f"{CROSSREF_BASE_URL}/works?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if not data:
        return []

    items = data.get("message", {}).get("items", [])
    works = []
    for item in items:
        work = _transform_work(item)
        if work:
            works.append(work)

    return works


def get_work(doi: str) -> Optional[dict]:
    """
    Get details for a specific work by DOI.

    Args:
        doi: DOI string (e.g., "10.1234/example")

    Returns:
        Work dictionary or None if not found
    """
    url = f"{CROSSREF_BASE_URL}/works/{urllib.parse.quote(doi, safe='')}"

    data = _make_request(url)
    if not data:
        return None

    item = data.get("message", {})
    return _transform_work(item)


def format_citation(work: dict) -> str:
    """Format a work dictionary as a citation string."""
    authors = work.get("authors", [])
    if len(authors) > 3:
        author_str = f"{authors[0]} et al."
    elif authors:
        author_str = ", ".join(authors)
    else:
        author_str = "Unknown"

    title = work.get("title", "No title")
    journal = work.get("journal", "")
    year = work.get("year", "")

    citation = f"{author_str}. {title}."
    if journal:
        citation += f" {journal}."
    if year:
        citation += f" {year}."

    return citation


# Command-line interface for testing
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crossref.py <search query>")
        print("Example: python crossref.py 'machine learning drug discovery'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching Crossref for: {query}\n")

    works = search_crossref(query, max_results=5)

    if not works:
        print(f'No results found for: "{query}"')
    else:
        for i, work in enumerate(works, 1):
            print(f"{i}. {work['title']}")
            print(f"   {format_citation(work)}")
            print(f"   Citations: {work['cited_by_count']}")
            if work["doi"]:
                print(f"   DOI: {work['doi']}")
            print(f"   Type: {work['type']}")
            print()
