#!/usr/bin/env python3
"""Search the literature: PubMed, Europe PMC (incl. preprints) or OpenAlex.

Usage:
  python3 scripts/search.py pubmed    "PPARA knockout liver steatosis" --max 20
  python3 scripts/search.py europepmc "hepatic lipid metabolism review" --max 20 [--preprints]
  python3 scripts/search.py openalex  "fatty acid oxidation mouse liver" --max 20

What it prints: one block per result with title, first author, year, journal,
DOI, PMID, PMCID, open access yes/no, and RETRACTED when the database marks it.
OpenAlex also prints a legal open-access link (oa link) when it knows one, for
papers that are open but not in PubMed Central (publisher site, repository, preprint).
Identifiers come from the database, so the Librarian never needs to recall one.

If the search fails it prints "SEARCH FAILED: <reason>" and exits with code 2.
"Found 0 results" means the search worked and found nothing. The two are
different and must be logged differently.
"""
import argparse
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _http import FetchError, fetch_json  # noqa: E402
from _md import utf8_console  # noqa: E402


def pubmed(q, n):
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = fetch_json(base + "esearch.fcgi?db=pubmed&retmode=json&sort=relevance&retmax=%d&term=%s" % (n, urllib.parse.quote(q)))
    ids = r.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    s = fetch_json(base + "esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(ids))["result"]
    out = []
    for i in ids:
        d = s.get(i, {})
        aid = {a.get("idtype"): a.get("value") for a in d.get("articleids", [])}
        out.append(dict(title=d.get("title", ""), first=(d.get("authors") or [{}])[0].get("name", ""),
                        year=(d.get("pubdate") or "")[:4], journal=d.get("source", ""), doi=aid.get("doi", ""),
                        pmid=i, pmcid=aid.get("pmc", ""), oa="yes" if aid.get("pmc") else "unknown",
                        retracted="Retracted Publication" in (d.get("pubtype") or []),
                        types=", ".join(d.get("pubtype") or [])))
    return out


def europepmc(q, n, preprints=False):
    query = q + (" AND SRC:PPR" if preprints else "")
    r = fetch_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=core&pageSize=%d&query=%s" % (n, urllib.parse.quote(query)))
    out = []
    for d in r.get("resultList", {}).get("result", []):
        types = (d.get("pubTypeList") or {}).get("pubType", [])
        out.append(dict(title=d.get("title", ""), first=(d.get("authorString") or "").split(",")[0],
                        year=d.get("pubYear", ""), journal=(d.get("journalInfo") or {}).get("journal", {}).get("title", "") or d.get("bookOrReportDetails", {}).get("publisher", "") or ("preprint" if d.get("source") == "PPR" else ""),
                        doi=d.get("doi", ""), pmid=d.get("pmid", ""), pmcid=d.get("pmcid", ""),
                        oa="yes" if d.get("isOpenAccess") == "Y" else "no",
                        retracted=any("retracted" in t.lower() for t in types), types=", ".join(types)))
    return out


def openalex(q, n):
    r = fetch_json("https://api.openalex.org/works?per-page=%d&search=%s" % (min(n, 50), urllib.parse.quote(q)))
    out = []
    for d in r.get("results", []):
        ids = d.get("ids") or {}
        auth = (d.get("authorships") or [{}])[0].get("author", {}).get("display_name", "")
        src = ((d.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        out.append(dict(title=d.get("display_name", ""), first=auth, year=str(d.get("publication_year", "")), journal=src,
                        doi=(d.get("doi") or "").replace("https://doi.org/", ""), pmid=(ids.get("pmid") or "").rsplit("/", 1)[-1],
                        pmcid=(ids.get("pmcid") or "").rsplit("/", 1)[-1], oa="yes" if (d.get("open_access") or {}).get("is_oa") else "no",
                        retracted=bool(d.get("is_retracted")), types=d.get("type", ""),
                        oa_url=((d.get("best_oa_location") or {}).get("pdf_url") or (d.get("best_oa_location") or {}).get("landing_page_url")
                                or (d.get("open_access") or {}).get("oa_url") or ""),
                        version=(d.get("best_oa_location") or {}).get("version") or ""))
    return out


def main():
    utf8_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("db", choices=["pubmed", "europepmc", "openalex"])
    ap.add_argument("query")
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--preprints", action="store_true")
    a = ap.parse_args()
    try:
        res = {"pubmed": lambda: pubmed(a.query, a.max), "openalex": lambda: openalex(a.query, a.max),
               "europepmc": lambda: europepmc(a.query, a.max, a.preprints)}[a.db]()
    except FetchError as e:
        print(f"SEARCH FAILED: {a.db}: {e}")
        sys.exit(2)
    print(f"Found {len(res)} results ({a.db}; query: {a.query})")
    for k, d in enumerate(res, 1):
        flag = "  ** RETRACTED **" if d["retracted"] else ""
        print(f"\n[{k}] {d['title']}{flag}\n    {d['first']} · {d['year']} · {d['journal']}\n"
              f"    DOI: {d['doi'] or '-'} · PMID: {d['pmid'] or '-'} · PMCID: {d['pmcid'] or '-'} · open access: {d['oa']}"
              + (f"\n    oa link: {d['oa_url']}" + (f" ({d['version']}; may differ from the published version)" if d.get('version') and d['version'] != 'publishedVersion' else "") if d.get("oa_url") else "")
              + (f"\n    type: {d['types']}" if d["types"] else ""))


if __name__ == "__main__":
    main()
