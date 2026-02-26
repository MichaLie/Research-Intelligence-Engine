"""
Unified Literature Search

Searches multiple academic databases and deduplicates results.
Combines: PubMed, OpenAlex, Semantic Scholar, arXiv, Crossref, DBLP, bioRxiv.

Usage:
    python3 skills/search_all.py "your search query"
    python3 skills/search_all.py "your search query" --sources pubmed,openalex,arxiv
    python3 skills/search_all.py "your search query" --sources all --max-results 10
"""

import sys
import os
import re
import json
import argparse
from typing import Optional

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_MAX_RESULTS, DOMAIN_DEFAULT_SOURCES

# All available sources
ALL_SOURCES = ["pubmed", "openalex", "semantic_scholar", "arxiv", "crossref", "dblp", "biorxiv"]

# Default sources (fallback when no domain specified)
DEFAULT_SOURCES = ["openalex", "semantic_scholar", "crossref"]


def _get_default_sources(domain: str | None = None) -> list[str]:
    """Get default sources for a domain. Falls back to DEFAULT_SOURCES."""
    if domain and domain in DOMAIN_DEFAULT_SOURCES:
        return list(DOMAIN_DEFAULT_SOURCES[domain])
    return list(DEFAULT_SOURCES)

# Minimal stop words for relevance scoring
_STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
    "were", "been", "have", "has", "had", "not", "but", "its", "can",
    "may", "will", "all", "each", "which", "their", "there", "about",
    "into", "than", "also", "how", "use", "using", "used", "based",
}


# ── Normalization functions ──────────────────────────────────────────────────
# Map each source's native format to a common format for deduplication.

def _normalize_pubmed(papers: list[dict]) -> list[dict]:
    """Normalize PubMed papers to common format."""
    normalized = []
    for p in papers:
        normalized.append({
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year", ""),
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi", ""),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}" if p.get("pmid") else "",
            "journal": p.get("journal", ""),
            "cited_by_count": 0,
            "source": "pubmed",
            # Preserve original fields
            "pmid": p.get("pmid", ""),
            "article_type": p.get("article_type", []),
        })
    return normalized


def _normalize_openalex(papers: list[dict]) -> list[dict]:
    """Normalize OpenAlex papers to common format."""
    normalized = []
    for p in papers:
        normalized.append({
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year", ""),
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "journal": p.get("journal", ""),
            "cited_by_count": p.get("cited_by_count", 0),
            "source": "openalex",
            # Preserve original fields
            "openalex_id": p.get("id", ""),
            "open_access": p.get("open_access", False),
        })
    return normalized


def _normalize_semantic_scholar(papers: list[dict]) -> list[dict]:
    """Normalize Semantic Scholar papers to common format."""
    normalized = []
    for p in papers:
        normalized.append({
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year", ""),
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "journal": p.get("venue", ""),
            "cited_by_count": p.get("cited_by_count", 0),
            "source": "semantic_scholar",
            # Preserve original fields
            "paper_id": p.get("paper_id", ""),
            "arxiv_id": p.get("arxiv_id", ""),
        })
    return normalized


def _normalize_arxiv(papers: list[dict]) -> list[dict]:
    """Normalize arXiv papers to common format."""
    normalized = []
    for p in papers:
        normalized.append({
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year", ""),
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "journal": f"arXiv ({p.get('primary_category', '')})" if p.get("primary_category") else "arXiv",
            "cited_by_count": 0,
            "source": "arxiv",
            # Preserve original fields
            "arxiv_id": p.get("arxiv_id", ""),
            "categories": p.get("categories", []),
            "pdf_url": p.get("pdf_url", ""),
        })
    return normalized


def _normalize_crossref(papers: list[dict]) -> list[dict]:
    """Normalize Crossref papers to common format."""
    normalized = []
    for p in papers:
        normalized.append({
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year", ""),
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "journal": p.get("journal", ""),
            "cited_by_count": p.get("cited_by_count", 0),
            "source": "crossref",
        })
    return normalized


def _normalize_dblp(papers: list[dict]) -> list[dict]:
    """Normalize DBLP papers to common format."""
    normalized = []
    for p in papers:
        normalized.append({
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year", ""),
            "abstract": "",  # DBLP has no abstracts
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "journal": p.get("venue", ""),
            "cited_by_count": 0,
            "source": "dblp",
            # Preserve original fields
            "dblp_key": p.get("dblp_key", ""),
        })
    return normalized


def _normalize_biorxiv(papers: list[dict]) -> list[dict]:
    """Normalize bioRxiv papers to common format."""
    normalized = []
    for p in papers:
        # bioRxiv authors field is a string, not a list
        authors = p.get("authors", "")
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(";") if a.strip()] if authors else []

        # Extract year from date
        year = p.get("date", "")[:4] if p.get("date") else ""

        normalized.append({
            "title": p.get("title", ""),
            "authors": authors,
            "year": year,
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi", ""),
            "url": p.get("url", ""),
            "journal": f"{p.get('server', 'biorxiv')} ({p.get('category', '')})",
            "cited_by_count": 0,
            "source": p.get("server", "biorxiv"),
        })
    return normalized


# ── Deduplication ────────────────────────────────────────────────────────────

def _normalize_title(title: str) -> str:
    """Normalize title for deduplication comparison."""
    normalized = title.lower()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = ' '.join(normalized.split())
    return normalized


def _metadata_score(paper: dict) -> int:
    """Score a paper by metadata richness for picking the best duplicate."""
    score = 0
    if paper.get("abstract"):
        score += 2
    score += min(paper.get("cited_by_count") or 0, 1000)
    if paper.get("doi"):
        score += 1
    if paper.get("journal"):
        score += 1
    return score


def _deduplicate(papers: list[dict]) -> list[dict]:
    """
    Deduplicate papers by DOI and normalized title.
    When a duplicate is found, keep the copy with richer metadata.
    """
    seen_dois: set = set()
    seen_titles: dict = {}  # norm_title -> index in unique_papers
    unique_papers: list[dict] = []

    for paper in papers:
        doi = (paper.get("doi") or "").lower().strip()
        title = (paper.get("title") or "").strip()
        norm_title = _normalize_title(title) if title else ""

        # Check for duplicate
        is_dup = False
        if doi and doi in seen_dois:
            is_dup = True
        if norm_title and norm_title in seen_titles:
            is_dup = True

        if is_dup:
            # Replace existing copy if the new one has richer metadata
            if norm_title and norm_title in seen_titles:
                idx = seen_titles[norm_title]
                if _metadata_score(paper) > _metadata_score(unique_papers[idx]):
                    unique_papers[idx] = paper
            continue

        # New paper: register identifiers
        idx = len(unique_papers)
        if doi:
            seen_dois.add(doi)
        if norm_title:
            seen_titles[norm_title] = idx
        unique_papers.append(paper)

    return unique_papers


# ── Relevance scoring ────────────────────────────────────────────────────────

def _relevance_score(query: str, paper: dict) -> float:
    """Score paper relevance using keyword overlap on title + abstract."""
    q_words = set(
        w for w in re.sub(r"[^\w\s]", " ", query.lower()).split()
        if len(w) >= 3 and w not in _STOP_WORDS
    )
    if not q_words:
        return 0.0

    title = (paper.get("title") or "").lower()
    abstract = (paper.get("abstract") or "").lower()
    text = f"{title} {abstract}"

    hits = sum(1 for w in q_words if w in text)
    base_score = hits / len(q_words)

    # Phrase bonus: check if 2-word sub-phrases from query appear intact
    query_clean = re.sub(r"[^\w\s]", " ", query.lower())
    words = [w for w in query_clean.split() if len(w) >= 3 and w not in _STOP_WORDS]
    phrase_bonus = 0.0
    if len(words) >= 2:
        bigrams_checked = 0
        bigrams_found = 0
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            bigrams_checked += 1
            if bigram in text:
                bigrams_found += 1
        if bigrams_checked > 0:
            phrase_bonus = 0.2 * (bigrams_found / bigrams_checked)

    return min(base_score + phrase_bonus, 1.0)


# ── Main search function ────────────────────────────────────────────────────

def search_all(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    sources: Optional[list[str]] = None,
    domain: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> dict:
    """
    Search multiple academic databases and return deduplicated results.

    Args:
        query: Search query string
        max_results: Maximum total results to return
        sources: List of sources to search (overrides domain defaults if set)
        domain: Research domain for automatic source selection
                (biomedical, computer_science, physics_math, social_sciences, general)
        year_from: Filter by publication year (start)
        year_to: Filter by publication year (end)

    Returns:
        Dictionary with:
        - data: List of deduplicated, scored papers
        - stats: Search statistics per source
    """
    if sources is None:
        sources = _get_default_sources(domain)

    all_papers = []
    stats = {"per_source": {}, "total_before_dedup": 0}

    for source in sources:
        try:
            papers = _search_source(source, query, max_results, year_from, year_to)
            all_papers.extend(papers)
            stats["per_source"][source] = {"count": len(papers)}
            stats["total_before_dedup"] += len(papers)
        except Exception as e:
            print(f"[WARNING] {source} search failed: {e}", file=sys.stderr)
            stats["per_source"][source] = {"error": str(e)}

    # Deduplicate
    unique = _deduplicate(all_papers)
    stats["total_after_dedup"] = len(unique)
    stats["duplicates_removed"] = stats["total_before_dedup"] - len(unique)

    # Score and sort by relevance
    for p in unique:
        p["relevance_score"] = _relevance_score(query, p)

    # Filter out clearly irrelevant papers (zero keyword overlap and low citations)
    unique = [
        p for p in unique
        if p["relevance_score"] > 0 or (p.get("cited_by_count") or 0) >= 50
    ]

    unique.sort(
        key=lambda p: (
            p["relevance_score"],
            min(p.get("cited_by_count") or 0, 5000),
            int(p.get("year") or 0),
        ),
        reverse=True,
    )

    final = unique[:max_results]

    return {
        "data": final,
        "stats": stats,
    }


def _search_source(source: str, query: str, max_results: int, year_from: Optional[int], year_to: Optional[int]) -> list[dict]:
    """Search a single source and return normalized papers."""
    if source == "pubmed":
        from skills.pubmed import search_and_fetch
        papers = search_and_fetch(query, max_results=max_results)
        return _normalize_pubmed(papers)

    elif source == "openalex":
        from skills.openalex import search_works
        papers = search_works(query, max_results=max_results, year_from=year_from, year_to=year_to)
        return _normalize_openalex(papers)

    elif source == "semantic_scholar":
        from skills.semantic_scholar import search_papers
        papers = search_papers(query, max_results=max_results, year_from=year_from, year_to=year_to)
        return _normalize_semantic_scholar(papers)

    elif source == "arxiv":
        from skills.arxiv import search_arxiv
        papers = search_arxiv(query, max_results=max_results, year_from=year_from, year_to=year_to)
        return _normalize_arxiv(papers)

    elif source == "crossref":
        from skills.crossref import search_crossref
        papers = search_crossref(query, max_results=max_results, year_from=year_from, year_to=year_to)
        return _normalize_crossref(papers)

    elif source == "dblp":
        from skills.dblp import search_dblp
        papers = search_dblp(query, max_results=max_results, year_from=year_from, year_to=year_to)
        return _normalize_dblp(papers)

    elif source == "biorxiv":
        from skills.biorxiv import search_biorxiv
        papers = search_biorxiv(query, max_results=max_results)
        return _normalize_biorxiv(papers)

    else:
        print(f"[WARNING] Unknown source: {source}", file=sys.stderr)
        return []


def _format_paper(paper: dict, index: int) -> str:
    """Format a single paper for CLI output."""
    lines = [f"{index}. {paper.get('title', 'No title')}"]

    authors = paper.get("authors", [])
    if authors:
        if len(authors) > 3:
            author_str = f"{authors[0]} et al."
        else:
            author_str = ", ".join(str(a) for a in authors)
        lines.append(f"   Authors: {author_str}")

    if paper.get("year"):
        lines.append(f"   Year: {paper['year']}")
    if paper.get("journal"):
        lines.append(f"   Journal: {paper['journal']}")
    if paper.get("cited_by_count"):
        lines.append(f"   Citations: {paper['cited_by_count']}")
    if paper.get("doi"):
        lines.append(f"   DOI: {paper['doi']}")
    if paper.get("source"):
        lines.append(f"   Source: {paper['source']}")
    if paper.get("relevance_score"):
        lines.append(f"   Relevance: {paper['relevance_score']:.2f}")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unified literature search across multiple academic databases"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCES),
        help=f"Comma-separated list of sources, or 'all'. Available: {', '.join(ALL_SOURCES)} (default: {', '.join(DEFAULT_SOURCES)})"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Maximum number of results (default: {DEFAULT_MAX_RESULTS})"
    )
    parser.add_argument(
        "--domain",
        default=None,
        choices=list(DOMAIN_DEFAULT_SOURCES.keys()),
        help=f"Research domain for default source selection. Overridden by --sources. Available: {', '.join(DOMAIN_DEFAULT_SOURCES.keys())}"
    )
    parser.add_argument("--year-from", type=int, help="Filter by publication year (start)")
    parser.add_argument("--year-to", type=int, help="Filter by publication year (end)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Parse sources: explicit --sources overrides --domain
    sources_explicitly_set = args.sources != ",".join(DEFAULT_SOURCES)
    if args.sources.lower() == "all":
        sources = list(ALL_SOURCES)
    elif sources_explicitly_set:
        sources = [s.strip() for s in args.sources.split(",")]
    elif args.domain:
        sources = _get_default_sources(args.domain)
    else:
        sources = list(DEFAULT_SOURCES)

    domain_info = f" [domain: {args.domain}]" if args.domain else ""
    print(f"Searching {', '.join(sources)} for: {args.query}{domain_info}\n")

    result = search_all(
        query=args.query,
        max_results=args.max_results,
        sources=sources,
        domain=args.domain,
        year_from=args.year_from,
        year_to=args.year_to,
    )

    papers = result["data"]
    stats = result["stats"]

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        # Print stats
        print(f"--- Search Statistics ---")
        for src, info in stats.get("per_source", {}).items():
            if "error" in info:
                print(f"  {src}: ERROR - {info['error']}")
            else:
                print(f"  {src}: {info['count']} results")
        print(f"  Total before dedup: {stats.get('total_before_dedup', 0)}")
        print(f"  Total after dedup: {stats.get('total_after_dedup', 0)}")
        print(f"  Duplicates removed: {stats.get('duplicates_removed', 0)}")
        print(f"  Final results: {len(papers)}")
        print()

        if not papers:
            print(f'No results found for: "{args.query}"')
        else:
            for i, paper in enumerate(papers, 1):
                print(_format_paper(paper, i))
                print()
