"""
arXiv Search Helper

Provides functions to search arXiv for preprints and papers.
No API key required. Rate limited to 1 request per 3 seconds (arXiv policy).

Usage:
    from skills.arxiv import search_arxiv, get_paper

    papers = search_arxiv("transformer attention mechanism", max_results=20)
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import time
import re
from typing import Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ARXIV_BASE_URL, DEFAULT_MAX_RESULTS


def _create_unverified_ssl_context():
    """Create unverified SSL context for systems with certificate issues."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


_SSL_CONTEXT = _create_unverified_ssl_context()

# Rate limiting: arXiv requires 3 seconds between requests
_last_request_time = 0.0
_MIN_REQUEST_INTERVAL = 3.0


def _rate_limit():
    """Ensure we respect arXiv's rate limit policy."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _urlopen_with_retry(url: str, timeout: int = 30, max_retries: int = 3) -> Optional[str]:
    """Make HTTP request with retry and exponential backoff."""
    for attempt in range(max_retries):
        try:
            _rate_limit()
            with urllib.request.urlopen(url, timeout=timeout, context=_SSL_CONTEXT) as response:
                return response.read().decode()
        except urllib.error.HTTPError as e:
            print(f"[WARNING] arXiv HTTP {e.code}, attempt {attempt + 1}/{max_retries}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"[ERROR] arXiv request failed: {e}", file=sys.stderr)
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[WARNING] arXiv request failed, retrying: {e}", file=sys.stderr)
                time.sleep(1)
                continue
            print(f"[ERROR] arXiv request failed: {e}", file=sys.stderr)
            return None

    return None


# Clark notation for Atom XML namespaces
_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"


def _parse_entry(entry: ET.Element) -> Optional[dict]:
    """Parse a single arXiv Atom entry into a paper dictionary."""
    try:
        a = _ATOM_NS
        arxiv_ns = _ARXIV_NS

        # Extract arXiv ID from id URL
        id_elem = entry.find(f"{{{a}}}id")
        arxiv_url = (id_elem.text or "").strip() if id_elem is not None else ""
        arxiv_id = ""
        if arxiv_url:
            match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', arxiv_url)
            if match:
                arxiv_id = match.group(1)

        # Title
        title_elem = entry.find(f"{{{a}}}title")
        title = (title_elem.text or "").strip().replace("\n", " ") if title_elem is not None else ""
        if not title:
            return None

        # Abstract (summary)
        summary_elem = entry.find(f"{{{a}}}summary")
        abstract = (summary_elem.text or "").strip().replace("\n", " ") if summary_elem is not None else ""

        # Authors (flat list of strings for RIE consistency)
        authors = []
        for author_elem in entry.findall(f"{{{a}}}author"):
            name_elem = author_elem.find(f"{{{a}}}name")
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())

        # Published date → year
        published_elem = entry.find(f"{{{a}}}published")
        year = None
        if published_elem is not None and published_elem.text:
            try:
                year = int(published_elem.text[:4])
            except (ValueError, TypeError):
                pass

        # Categories
        categories = []
        for cat_elem in entry.findall(f"{{{a}}}category"):
            term = cat_elem.get("term")
            if term:
                categories.append(term)

        # Primary category
        primary_cat_elem = entry.find(f"{{{arxiv_ns}}}primary_category")
        primary_category = primary_cat_elem.get("term") if primary_cat_elem is not None else ""

        # DOI if available
        doi_elem = entry.find(f"{{{arxiv_ns}}}doi")
        doi = (doi_elem.text or "").strip() if doi_elem is not None else ""

        # PDF link
        pdf_url = ""
        for link_elem in entry.findall(f"{{{a}}}link"):
            if link_elem.get("title") == "pdf":
                pdf_url = link_elem.get("href", "") or ""
                break

        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": abstract,
            "doi": doi,
            "categories": categories,
            "primary_category": primary_category,
            "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else arxiv_url,
            "pdf_url": pdf_url,
            "ar5iv_url": f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}" if arxiv_id else "",
            "source": "arxiv",
        }

    except Exception as e:
        print(f"[WARNING] Failed to parse arXiv entry: {e}", file=sys.stderr)
        return None


def _parse_arxiv_response(xml_text: str) -> list[dict]:
    """Parse arXiv Atom XML response into list of papers."""
    papers = []
    try:
        root = ET.fromstring(xml_text)
        for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
            paper = _parse_entry(entry)
            if paper:
                papers.append(paper)
    except ET.ParseError as e:
        print(f"[ERROR] Failed to parse arXiv XML: {e}", file=sys.stderr)
    return papers


def search_arxiv(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    categories: Optional[list[str]] = None,
) -> list[dict]:
    """
    Search arXiv for preprints and papers.

    Args:
        query: Search query string
        max_results: Maximum number of results (max 100 recommended)
        year_from: Filter by publication year (start) — applied post-fetch
        year_to: Filter by publication year (end) — applied post-fetch
        categories: Optional list of arXiv categories (e.g., ['cs.LG', 'cs.AI'])

    Returns:
        List of paper dictionaries with keys:
        - arxiv_id: arXiv paper ID (e.g., "2301.12345")
        - title: Paper title
        - authors: List of author names
        - year: Publication year
        - abstract: Abstract text
        - doi: DOI (if available)
        - categories: List of arXiv categories
        - primary_category: Primary category
        - url: URL to the paper
        - pdf_url: URL to PDF
        - ar5iv_url: URL to HTML rendering
        - source: "arxiv"
    """
    if not query:
        return []

    # Clean query for arXiv API (remove special characters except hyphens)
    clean_query = re.sub(r'[^\w\s\-]', '', query).strip()

    # Build search query
    search_parts = [f"all:{clean_query}"]

    if categories:
        cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
        search_parts.append(f"({cat_query})")

    search_query = " AND ".join(search_parts)

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": min(max_results, 100),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    url = f"{ARXIV_BASE_URL}?{urllib.parse.urlencode(params)}"

    xml_text = _urlopen_with_retry(url)
    if not xml_text:
        return []

    papers = _parse_arxiv_response(xml_text)

    # Filter by year post-fetch (arXiv API doesn't support date range natively)
    if year_from or year_to:
        filtered = []
        for p in papers:
            y = p.get("year")
            if y is None:
                continue
            if year_from and y < year_from:
                continue
            if year_to and y > year_to:
                continue
            filtered.append(p)
        papers = filtered

    return papers


def get_paper(arxiv_id: str) -> Optional[dict]:
    """
    Get a specific paper by arXiv ID.

    Args:
        arxiv_id: arXiv paper ID (e.g., "2301.12345")

    Returns:
        Paper dictionary or None if not found
    """
    # Clean ID
    clean_id = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")

    params = {
        "id_list": clean_id,
        "max_results": 1,
    }

    url = f"{ARXIV_BASE_URL}?{urllib.parse.urlencode(params)}"

    xml_text = _urlopen_with_retry(url)
    if not xml_text:
        return None

    papers = _parse_arxiv_response(xml_text)
    return papers[0] if papers else None


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
    year = paper.get("year", "")
    arxiv_id = paper.get("arxiv_id", "")

    citation = f"{author_str}. {title}."
    if year:
        citation += f" {year}."
    if arxiv_id:
        citation += f" arXiv:{arxiv_id}."

    return citation


# Command-line interface for testing
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python arxiv.py <search query>")
        print("Example: python arxiv.py 'transformer attention mechanism'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching arXiv for: {query}\n")

    papers = search_arxiv(query, max_results=5)

    if not papers:
        print(f'No results found for: "{query}"')
    else:
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            print(f"   {format_citation(paper)}")
            cats = ", ".join(paper.get("categories", [])[:3])
            if cats:
                print(f"   Categories: {cats}")
            if paper["doi"]:
                print(f"   DOI: {paper['doi']}")
            print(f"   URL: {paper['url']}")
            print()
