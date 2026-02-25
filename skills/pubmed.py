"""
PubMed Search Helper

Provides functions to search PubMed via the NCBI E-utilities API.
No API key required for basic usage (rate limited to 3 requests/second).
With API key: 10 requests/second.

Usage:
    from skills.pubmed import search_pubmed, fetch_details

    # Search for articles
    ids = search_pubmed("intermittent fasting longevity", max_results=20)

    # Get article details
    articles = fetch_details(ids)
"""

import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import ssl
import time
from typing import Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PUBMED_BASE_URL, PUBMED_API_KEY, DEFAULT_MAX_RESULTS


def _create_unverified_ssl_context():
    """Create unverified SSL context for systems with certificate issues.

    This is acceptable for trusted APIs (PubMed, OpenAlex, bioRxiv).
    """
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


# Global SSL context - use unverified to avoid certificate issues on macOS
_SSL_CONTEXT = _create_unverified_ssl_context()


def _urlopen_with_ssl_fallback(url: str, timeout: int = 30):
    """Open URL with SSL context that handles certificate issues."""
    return urllib.request.urlopen(url, timeout=timeout, context=_SSL_CONTEXT)


# Rate limiting: track last request time
_last_request_time = 0.0
_MIN_REQUEST_INTERVAL = 0.34  # ~3 requests/second without API key


def _rate_limit():
    """Ensure we don't exceed rate limits (3 req/sec without key, 10 with key)."""
    global _last_request_time
    interval = 0.1 if PUBMED_API_KEY else _MIN_REQUEST_INTERVAL
    elapsed = time.time() - _last_request_time
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_time = time.time()


def search_pubmed(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    article_types: Optional[list] = None
) -> list[str]:
    """
    Search PubMed and return list of PMIDs.

    Args:
        query: Search query (supports PubMed syntax)
        max_results: Maximum number of results to return
        date_from: Start date (YYYY-MM-DD format, converted internally)
        date_to: End date (YYYY-MM-DD format, converted internally)
        article_types: List of article types to filter (e.g., ["review", "clinical trial"])

    Returns:
        List of PubMed IDs (PMIDs)

    Example:
        >>> ids = search_pubmed("CRISPR gene editing", max_results=10)
        >>> print(f"Found {len(ids)} articles")
    """
    # Build the query with any filters
    full_query = query

    if article_types:
        type_filter = " OR ".join([f'"{t}"[Publication Type]' for t in article_types])
        full_query = f"({query}) AND ({type_filter})"

    # Build URL parameters
    params = {
        "db": "pubmed",
        "term": full_query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance"
    }

    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY

    if date_from:
        params["datetype"] = "pdat"
        # Convert YYYY-MM-DD to YYYY/MM/DD for PubMed API
        params["mindate"] = date_from.replace("-", "/")

    if date_to:
        # Convert YYYY-MM-DD to YYYY/MM/DD for PubMed API
        params["maxdate"] = date_to.replace("-", "/")

    url = f"{PUBMED_BASE_URL}/esearch.fcgi?{urllib.parse.urlencode(params)}"

    try:
        _rate_limit()
        with _urlopen_with_ssl_fallback(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[ERROR] Failed searching PubMed: {e}", file=sys.stderr)
        return []


def fetch_details(pmids: list[str]) -> list[dict]:
    """
    Fetch detailed information for a list of PMIDs.

    Args:
        pmids: List of PubMed IDs

    Returns:
        List of article dictionaries with keys:
        - pmid: PubMed ID
        - title: Article title
        - authors: List of author names
        - journal: Journal name
        - year: Publication year
        - abstract: Article abstract
        - doi: DOI if available
        - article_type: Publication type(s)

    Example:
        >>> articles = fetch_details(["12345678", "87654321"])
        >>> for a in articles:
        ...     print(f"{a['title']} ({a['year']})")
    """
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }

    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY

    url = f"{PUBMED_BASE_URL}/efetch.fcgi?{urllib.parse.urlencode(params)}"

    try:
        _rate_limit()
        with _urlopen_with_ssl_fallback(url, timeout=30) as response:
            xml_data = response.read().decode()
            return _parse_pubmed_xml(xml_data)
    except Exception as e:
        print(f"[ERROR] Failed fetching PubMed details: {e}", file=sys.stderr)
        return []


def _parse_pubmed_xml(xml_data: str) -> list[dict]:
    """Parse PubMed XML response into article dictionaries."""
    articles = []

    try:
        root = ET.fromstring(xml_data)

        for article in root.findall(".//PubmedArticle"):
            article_data = {}

            # PMID
            pmid = article.find(".//PMID")
            article_data["pmid"] = pmid.text if pmid is not None else ""

            # Title
            title = article.find(".//ArticleTitle")
            article_data["title"] = title.text if title is not None else ""

            # Authors
            authors = []
            for author in article.findall(".//Author"):
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name = f"{forename.text} {name}"
                    authors.append(name)
            article_data["authors"] = authors

            # Journal
            journal = article.find(".//Journal/Title")
            article_data["journal"] = journal.text if journal is not None else ""

            # Year
            year = article.find(".//PubDate/Year")
            if year is None:
                year = article.find(".//PubDate/MedlineDate")
            article_data["year"] = year.text[:4] if year is not None and year.text else ""

            # Abstract
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join([p.text for p in abstract_parts if p.text])
            article_data["abstract"] = abstract

            # DOI
            doi = article.find(".//ArticleId[@IdType='doi']")
            article_data["doi"] = doi.text if doi is not None else ""

            # Publication types
            pub_types = []
            for pt in article.findall(".//PublicationType"):
                if pt.text:
                    pub_types.append(pt.text)
            article_data["article_type"] = pub_types

            articles.append(article_data)

    except ET.ParseError as e:
        print(f"[ERROR] Failed parsing PubMed XML: {e}", file=sys.stderr)

    return articles


def format_citation(article: dict) -> str:
    """
    Format an article dictionary as a citation string.

    Args:
        article: Article dictionary from fetch_details()

    Returns:
        Formatted citation string
    """
    authors = article.get("authors", [])
    if len(authors) > 3:
        author_str = f"{authors[0]} et al."
    elif authors:
        author_str = ", ".join(authors)
    else:
        author_str = "Unknown"

    title = article.get("title", "No title")
    journal = article.get("journal", "")
    year = article.get("year", "")

    return f"{author_str}. {title} {journal}. {year}."


def search_and_fetch(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    **kwargs
) -> list[dict]:
    """
    Convenience function: search and fetch details in one call.

    Args:
        query: Search query
        max_results: Maximum results
        **kwargs: Additional arguments passed to search_pubmed

    Returns:
        List of article dictionaries
    """
    pmids = search_pubmed(query, max_results=max_results, **kwargs)
    return fetch_details(pmids)


# Command-line interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pubmed.py <search query>")
        print("Example: python pubmed.py 'CRISPR gene therapy'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching PubMed for: {query}\n")

    articles = search_and_fetch(query, max_results=5)

    if not articles:
        print(f"No results found for: \"{query}\"")
        sys.exit(0)

    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   {format_citation(article)}")
        print(f"   PMID: {article['pmid']}")
        if article['doi']:
            print(f"   DOI: {article['doi']}")
        print()
