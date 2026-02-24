"""
OpenAlex Search Helper

Provides functions to search OpenAlex, a free and open catalog of scholarly works.
No API key required. Polite pool: include email in requests for higher rate limits.

Usage:
    from skills.openalex import search_works, get_work_details

    # Search for works
    works = search_works("machine learning drug discovery", max_results=20)

    # Get details for a specific work
    work = get_work_details("W2741809807")
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
from config import OPENALEX_BASE_URL, OPENALEX_EMAIL, DEFAULT_MAX_RESULTS


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
    if OPENALEX_EMAIL:
        headers["User-Agent"] = f"ResearchEngine/1.0 (mailto:{OPENALEX_EMAIL})"
    return headers


# Rate limiting: OpenAlex allows 10 req/sec for polite pool, ~1 req/sec otherwise
_last_request_time = 0.0


def _rate_limit():
    """Ensure we don't exceed rate limits."""
    global _last_request_time
    interval = 0.1 if OPENALEX_EMAIL else 1.0  # 10/sec with email, 1/sec without
    elapsed = time.time() - _last_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_time = time.time()


def _make_request(url: str) -> Optional[dict]:
    """Make a request to OpenAlex API."""
    headers = _build_headers()
    request = urllib.request.Request(url, headers=headers)

    try:
        _rate_limit()
        with urllib.request.urlopen(request, timeout=30, context=_SSL_CONTEXT) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error making OpenAlex request: {e}")
        return None


def search_works(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    work_type: Optional[str] = None,
    open_access: Optional[bool] = None,
    sort_by: str = "relevance_score:desc",
    cited_by_count_min: Optional[int] = None
) -> list[dict]:
    """
    Search OpenAlex for scholarly works.

    Args:
        query: Search query (searches title and abstract)
        max_results: Maximum number of results
        year_from: Filter by publication year (start)
        year_to: Filter by publication year (end)
        work_type: Filter by type (article, review, book-chapter, etc.)
        open_access: Filter by open access status
        sort_by: Sort order (relevance_score:desc, cited_by_count:desc, publication_date:desc)
        cited_by_count_min: Minimum citation count filter

    Returns:
        List of work dictionaries with keys:
        - id: OpenAlex ID
        - doi: DOI
        - title: Work title
        - authors: List of author names
        - year: Publication year
        - journal: Journal/venue name
        - abstract: Abstract (if available)
        - cited_by_count: Number of citations
        - type: Work type
        - open_access: Open access status
        - url: URL to the work

    Example:
        >>> works = search_works("protein folding", max_results=10)
        >>> for w in works:
        ...     print(f"{w['title']} ({w['year']}) - {w['cited_by_count']} citations")
    """
    # Build filter string
    filters = []

    if year_from:
        filters.append(f"publication_year:>{year_from-1}")
    if year_to:
        filters.append(f"publication_year:<{year_to+1}")
    if work_type:
        filters.append(f"type:{work_type}")
    if open_access is not None:
        filters.append(f"open_access.is_oa:{str(open_access).lower()}")
    if cited_by_count_min:
        filters.append(f"cited_by_count:>{cited_by_count_min-1}")

    # Build URL
    params = {
        "search": query,
        "per_page": min(max_results, 50),  # OpenAlex max is 50 per page
        "sort": sort_by
    }

    if filters:
        params["filter"] = ",".join(filters)

    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    url = f"{OPENALEX_BASE_URL}/works?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if not data:
        return []

    works = []
    for item in data.get("results", []):
        works.append(_parse_work(item))

    return works


def _parse_work(item: dict) -> dict:
    """Parse an OpenAlex work item into a standardized dictionary."""
    # Extract authors
    authors = []
    for authorship in item.get("authorships", []):
        author = authorship.get("author", {})
        if author.get("display_name"):
            authors.append(author["display_name"])

    # Extract journal/venue
    primary_location = item.get("primary_location", {}) or {}
    source = primary_location.get("source", {}) or {}
    journal = source.get("display_name", "")

    # Extract abstract (OpenAlex provides inverted index)
    abstract = ""
    abstract_inverted_index = item.get("abstract_inverted_index", {})
    if abstract_inverted_index:
        abstract = _reconstruct_abstract(abstract_inverted_index)

    return {
        "id": item.get("id", "").replace("https://openalex.org/", ""),
        "doi": (item.get("doi") or "").replace("https://doi.org/", ""),
        "title": item.get("title", ""),
        "authors": authors,
        "year": item.get("publication_year"),
        "journal": journal,
        "abstract": abstract,
        "cited_by_count": item.get("cited_by_count", 0),
        "type": item.get("type", ""),
        "open_access": item.get("open_access", {}).get("is_oa", False),
        "url": item.get("doi") or item.get("id", "")
    }


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return ""

    # Create list of (position, word) tuples
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))

    # Sort by position and join
    word_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in word_positions)


def get_work_details(work_id: str) -> Optional[dict]:
    """
    Get detailed information for a specific work.

    Args:
        work_id: OpenAlex work ID (e.g., "W2741809807") or DOI

    Returns:
        Work dictionary or None if not found
    """
    # Handle DOI input
    if work_id.startswith("10."):
        work_id = f"https://doi.org/{work_id}"

    params = {}
    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    url = f"{OPENALEX_BASE_URL}/works/{work_id}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if data:
        return _parse_work(data)
    return None


def get_citing_works(work_id: str, max_results: int = DEFAULT_MAX_RESULTS) -> list[dict]:
    """
    Get works that cite a specific work.

    Args:
        work_id: OpenAlex work ID or DOI
        max_results: Maximum number of results

    Returns:
        List of citing work dictionaries
    """
    params = {
        "filter": f"cites:{work_id}",
        "per_page": min(max_results, 50),
        "sort": "cited_by_count:desc"
    }

    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    url = f"{OPENALEX_BASE_URL}/works?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if not data:
        return []

    return [_parse_work(item) for item in data.get("results", [])]


def search_authors(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS
) -> list[dict]:
    """
    Search for authors in OpenAlex.

    Args:
        query: Author name to search
        max_results: Maximum number of results

    Returns:
        List of author dictionaries
    """
    params = {
        "search": query,
        "per_page": min(max_results, 50)
    }

    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    url = f"{OPENALEX_BASE_URL}/authors?{urllib.parse.urlencode(params)}"

    data = _make_request(url)
    if not data:
        return []

    authors = []
    for item in data.get("results", []):
        authors.append({
            "id": item.get("id", "").replace("https://openalex.org/", ""),
            "name": item.get("display_name", ""),
            "works_count": item.get("works_count", 0),
            "cited_by_count": item.get("cited_by_count", 0),
            "institution": (item.get("last_known_institution") or {}).get("display_name", ""),
            "orcid": item.get("orcid", "")
        })

    return authors


def format_citation(work: dict) -> str:
    """
    Format a work dictionary as a citation string.

    Args:
        work: Work dictionary from search functions

    Returns:
        Formatted citation string
    """
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
    import sys

    if len(sys.argv) < 2:
        print("Usage: python openalex.py <search query>")
        print("Example: python openalex.py 'deep learning protein structure'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching OpenAlex for: {query}\n")

    works = search_works(query, max_results=5)

    if not works:
        print("No results found.")
    else:
        for i, work in enumerate(works, 1):
            print(f"{i}. {work['title']}")
            print(f"   {format_citation(work)}")
            print(f"   Citations: {work['cited_by_count']}")
            print(f"   Open Access: {work['open_access']}")
            if work['doi']:
                print(f"   DOI: {work['doi']}")
            print()
