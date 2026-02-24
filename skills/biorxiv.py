"""
bioRxiv/medRxiv Search Helper

Provides functions to search bioRxiv and medRxiv preprint servers.
Uses the bioRxiv API (https://api.biorxiv.org/).

Usage:
    from skills.biorxiv import search_biorxiv, search_medrxiv

    # Search bioRxiv
    papers = search_biorxiv("CRISPR", max_results=20)

    # Search medRxiv
    papers = search_medrxiv("COVID-19 vaccine", max_results=20)
"""

import urllib.request
import urllib.parse
import json
import ssl
from datetime import datetime, timedelta
from typing import Optional
import time
import re
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BIORXIV_BASE_URL, DEFAULT_MAX_RESULTS


def _create_unverified_ssl_context():
    """Create unverified SSL context for systems with certificate issues."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


_SSL_CONTEXT = _create_unverified_ssl_context()


def search_biorxiv(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    server: str = "biorxiv"
) -> list[dict]:
    """
    Search bioRxiv or medRxiv for preprints.

    Args:
        query: Search query (searches title and abstract)
        max_results: Maximum number of results
        date_from: Start date (YYYY-MM-DD format), defaults to 1 year ago
        date_to: End date (YYYY-MM-DD format), defaults to today
        server: "biorxiv" or "medrxiv"

    Returns:
        List of paper dictionaries with keys:
        - doi: DOI of the preprint
        - title: Paper title
        - authors: Author string
        - abstract: Paper abstract
        - date: Publication date
        - category: Subject category
        - url: URL to the paper
        - version: Version number

    Example:
        >>> papers = search_biorxiv("gene therapy", max_results=5)
        >>> for p in papers:
        ...     print(f"{p['title']} ({p['date']})")
    """
    # Default date range: last year
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    if not date_from:
        date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # bioRxiv API uses a details endpoint with date range
    # We'll fetch recent papers and filter by query
    url = f"{BIORXIV_BASE_URL}/details/{server}/{date_from}/{date_to}/0/json"

    papers = []
    cursor = 0

    # Split query into words for multi-word matching
    # All words must appear (AND logic), case-insensitive
    query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]

    while len(papers) < max_results:
        paginated_url = f"{BIORXIV_BASE_URL}/details/{server}/{date_from}/{date_to}/{cursor}/json"

        try:
            with urllib.request.urlopen(paginated_url, timeout=30, context=_SSL_CONTEXT) as response:
                data = json.loads(response.read().decode())

                collection = data.get("collection", [])
                if not collection:
                    break

                for item in collection:
                    # Filter by query - ALL words must appear in title OR abstract
                    title = item.get("title", "").lower()
                    abstract = item.get("abstract", "").lower()
                    combined_text = title + " " + abstract

                    # Check if all query words are present
                    if all(word in combined_text for word in query_words):
                        papers.append({
                            "doi": item.get("doi", ""),
                            "title": item.get("title", ""),
                            "authors": item.get("authors", ""),
                            "abstract": item.get("abstract", ""),
                            "date": item.get("date", ""),
                            "category": item.get("category", ""),
                            "url": f"https://www.{server}.org/content/{item.get('doi', '')}",
                            "version": item.get("version", "1"),
                            "server": server
                        })

                        if len(papers) >= max_results:
                            break

                # Move to next page (100 results per page)
                cursor += 100

                # Rate limiting: pause between requests to avoid overloading API
                time.sleep(0.5)

                # Safety limit to prevent infinite loops
                if cursor > 1000:
                    break

        except Exception as e:
            print(f"Error searching {server}: {e}")
            break

    return papers[:max_results]


def search_medrxiv(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> list[dict]:
    """
    Search medRxiv for preprints.

    Convenience wrapper for search_biorxiv with server="medrxiv".

    Args:
        query: Search query
        max_results: Maximum number of results
        date_from: Start date (YYYY-MM-DD format)
        date_to: End date (YYYY-MM-DD format)

    Returns:
        List of paper dictionaries
    """
    return search_biorxiv(
        query=query,
        max_results=max_results,
        date_from=date_from,
        date_to=date_to,
        server="medrxiv"
    )


def get_paper_details(doi: str) -> Optional[dict]:
    """
    Get detailed information for a specific preprint by DOI.

    Args:
        doi: The DOI of the preprint (e.g., "10.1101/2024.01.01.123456")

    Returns:
        Paper dictionary or None if not found
    """
    # Extract the bioRxiv-specific part of the DOI
    if doi.startswith("10.1101/"):
        doi_suffix = doi[8:]  # Remove "10.1101/"
    else:
        doi_suffix = doi

    url = f"{BIORXIV_BASE_URL}/details/biorxiv/{doi_suffix}/na/json"

    try:
        with urllib.request.urlopen(url, timeout=30, context=_SSL_CONTEXT) as response:
            data = json.loads(response.read().decode())
            collection = data.get("collection", [])

            if collection:
                item = collection[0]
                return {
                    "doi": item.get("doi", ""),
                    "title": item.get("title", ""),
                    "authors": item.get("authors", ""),
                    "abstract": item.get("abstract", ""),
                    "date": item.get("date", ""),
                    "category": item.get("category", ""),
                    "url": f"https://www.biorxiv.org/content/{item.get('doi', '')}",
                    "version": item.get("version", "1"),
                    "published_doi": item.get("published", "")  # If published in journal
                }
    except Exception as e:
        print(f"Error fetching paper details: {e}")

    return None


def format_citation(paper: dict) -> str:
    """
    Format a paper dictionary as a citation string.

    Args:
        paper: Paper dictionary from search functions

    Returns:
        Formatted citation string
    """
    authors = paper.get("authors", "Unknown")
    # Truncate long author lists
    if len(authors) > 100:
        authors = authors[:100] + "..."

    title = paper.get("title", "No title")
    date = paper.get("date", "")
    server = paper.get("server", "bioRxiv")
    doi = paper.get("doi", "")

    return f"{authors}. {title}. {server} {date}. doi: {doi}"


def search_both_servers(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    **kwargs
) -> list[dict]:
    """
    Search both bioRxiv and medRxiv simultaneously.

    Args:
        query: Search query
        max_results: Maximum total results (split between servers)
        **kwargs: Additional arguments passed to search functions

    Returns:
        Combined list of papers from both servers, sorted by date
    """
    half_results = max_results // 2

    biorxiv_papers = search_biorxiv(query, max_results=half_results, **kwargs)
    medrxiv_papers = search_medrxiv(query, max_results=half_results, **kwargs)

    # Combine and sort by date (most recent first)
    all_papers = biorxiv_papers + medrxiv_papers
    all_papers.sort(key=lambda x: x.get("date", ""), reverse=True)

    return all_papers[:max_results]


# Command-line interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python biorxiv.py <search query>")
        print("Example: python biorxiv.py 'CRISPR gene editing'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching bioRxiv and medRxiv for: {query}\n")

    papers = search_both_servers(query, max_results=5)

    if not papers:
        print("No results found.")
    else:
        for i, paper in enumerate(papers, 1):
            print(f"{i}. [{paper.get('server', 'bioRxiv')}] {paper['title']}")
            print(f"   Date: {paper['date']}")
            print(f"   Category: {paper['category']}")
            print(f"   DOI: {paper['doi']}")
            print()
