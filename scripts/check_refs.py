#!/usr/bin/env python3
"""Check that every reference exists, is the paper it claims to be, and is not retracted.

Usage:
  python3 scripts/check_refs.py sessions/<slug>/my-papers.txt --out sessions/<slug>/refcheck-mine.md
  python3 scripts/check_refs.py --from-evidence sessions/<slug> --out sessions/<slug>/refcheck-evidence-r<N>.md

Input lines may hold a DOI (10.xxxx/...) and/or a PMID ("PMID 12345678"), optionally
followed by the title or note the researcher wrote; that text is compared with the real title.

What it checks, per identifier:
  - DOI: resolved at Crossref (title, journal, year) and Crossref's retraction records.
    DOIs that Crossref does not know (arXiv, Zenodo, Dryad, figshare ...) are looked up
    at DataCite, then at doi.org, before anything is called NOT FOUND.
  - PMID (given, or found from the DOI): PubMed's "Retracted Publication" type and
    its "RetractionIn" link to the notice.
  - Title match: if the line carries a title, the share of its words found in the real title.
Flags: RETRACTED · THIS IS A RETRACTION NOTICE · NOT FOUND · TITLE MISMATCH ·
DOI/PMID DISAGREE · NOT CHECKED (exists, but no metadata to check) · CHECK FAILED (network; not a verdict).
The same paper is listed once, even if several inputs name it (a DOI line and a PMID
line, or one paper in both evidence files).
"""
import argparse
import glob
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _http import FetchError, fetch, fetch_json  # noqa: E402

from _md import DOI_RE, utf8_console  # noqa: E402  (one DOI pattern for every script)
PMID_RE = re.compile(r"\bPMID[:\s]*?(\d{1,9})\b", re.I)
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
STOP = set("a an the of in and or for to on by with from at as is are be its their this that via into than".split())
NOTICE_TITLE = re.compile(r"^\s*(retraction(\s+note|\s+notice)?|notice of retraction|retraction of)\b\s*[:.]?", re.I)


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 2}


def cell(s):
    """Text safe inside a markdown table cell: no '|' and no line breaks."""
    return re.sub(r"\s+", " ", str(s or "")).replace("|", "/").strip()


def pubmed_record(pmid):
    x = fetch(EUTILS + f"efetch.fcgi?db=pubmed&retmode=xml&id={pmid}")
    if "<PubmedArticle>" not in x:
        return None
    title = re.sub(r"<[^>]+>", "", (re.findall(r"<ArticleTitle>(.*?)</ArticleTitle>", x, re.S) or [""])[0])
    types = re.findall(r"<PublicationType[^>]*>(.*?)</PublicationType>", x)
    notice = re.findall(r'<CommentsCorrections RefType="RetractionIn"[^>]*>\s*<RefSource>(.*?)</RefSource>', x, re.S)
    doi = (re.findall(r'<ArticleId IdType="doi">(.*?)</ArticleId>', x) or [""])[0]
    journal = (re.findall(r"<ISOAbbreviation>(.*?)</ISOAbbreviation>", x) or [""])[0]
    year = (re.findall(r"<PubDate>\s*<Year>(\d{4})", x) or re.findall(r"<Year>(\d{4})</Year>", x) or [""])[0]
    return dict(title=title.strip(), types=types, notice=notice[0].strip() if notice else "", doi=doi, journal=journal, year=year)


def pmid_for_doi(doi):
    r = fetch_json(EUTILS + "esearch.fcgi?db=pubmed&retmode=json&term=" + urllib.parse.quote(f"{doi}[doi]"))
    ids = r.get("esearchresult", {}).get("idlist", [])
    return ids[0] if len(ids) == 1 else ""


def crossref_retraction(m):
    """('retracted' | 'notice' | '', notice DOI). Retraction Watch data in Crossref links an
    article and its notice in both directions, so the publisher's own link and the
    title decide which of the two this record is."""
    def retr(key, publisher_only=False):
        return [u for u in (m.get(key) or []) if "retract" in (u.get("type") or "").lower()
                and (not publisher_only or (u.get("source") or "publisher") == "publisher")]
    title = (m.get("title") or [""])[0]
    by, to = retr("updated-by"), retr("update-to")
    if (m.get("type") or "") == "retraction" or retr("update-to", True) or NOTICE_TITLE.match(title) or (to and not by):
        return "notice", (to[0].get("DOI") if to else "")
    if by:
        return "retracted", by[0].get("DOI") or ""
    return "", ""


def datacite_or_handle(doi, row):
    """For a DOI Crossref does not know. Returns True if the DOI exists somewhere."""
    try:
        a = fetch_json("https://api.datacite.org/dois/" + urllib.parse.quote(doi))["data"]["attributes"]
        row.update(title=re.sub(r"\s+", " ", ((a.get("titles") or [{}])[0].get("title") or "")).strip(),
                   journal=a.get("publisher") if isinstance(a.get("publisher"), str) else (a.get("publisher") or {}).get("name", ""),
                   year=str(a.get("publicationYear") or ""))
        rel = [r for r in (a.get("relatedIdentifiers") or []) if "retract" in (r.get("relationType") or "").lower()]
        if rel:
            row["flags"].append("RETRACTED")
            row["status"] = "DataCite: " + rel[0].get("relationType", "") + " " + rel[0].get("relatedIdentifier", "")
        else:
            row["status"] = "registered at DataCite, not Crossref (DataCite rarely records retractions)"
        return True
    except FetchError as e:
        if "404" not in str(e):
            raise
    try:
        h = fetch_json("https://doi.org/api/handles/" + urllib.parse.quote(doi))
        if h.get("responseCode") == 1:
            row["flags"].append("NOT CHECKED")
            row["status"] = "the DOI exists at doi.org, but neither Crossref nor DataCite has its record; title and retraction not checked"
            return True
    except FetchError as e:
        if "404" not in str(e):
            raise
    return False


def check(doi, pmid, note):
    row = dict(ident=(f"DOI {doi}" if doi else "") + (" · " if doi and pmid else "") + (f"PMID {pmid}" if pmid else ""),
               title="", journal="", year="", status="", flags=[], doi=doi.lower())
    try:
        if doi:
            try:
                m = fetch_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
                row.update(title=re.sub(r"\s+", " ", (m.get("title") or [""])[0]).strip(), journal=(m.get("container-title") or [""])[0],
                           year=str(((m.get("issued") or {}).get("date-parts") or [[""]])[0][0]))
                kind, other = crossref_retraction(m)
                if kind == "retracted":
                    row["flags"].append("RETRACTED")
                    row["status"] = "Crossref retraction notice: " + other
                elif kind == "notice":
                    row["flags"].append("THIS IS A RETRACTION NOTICE")
                    row["status"] = "the notice for: " + other if other else "a retraction notice"
            except FetchError as e:
                if "404" not in str(e):
                    raise
                if not datacite_or_handle(doi, row):
                    row["flags"].append("NOT FOUND")
                    row["status"] = "DOI does not resolve at Crossref, DataCite or doi.org"
            if not pmid and "NOT FOUND" not in row["flags"]:
                pmid = pmid_for_doi(doi)
        if pmid:
            rec = pubmed_record(pmid)
            if rec is None:
                row["flags"].append("NOT FOUND")
                row["status"] = (row["status"] + "; " if row["status"] else "") + f"PMID {pmid} not in PubMed"
            else:
                if not row["title"]:
                    row.update(title=rec["title"], journal=rec["journal"], year=rec["year"])
                if "Retracted Publication" in rec["types"] and "THIS IS A RETRACTION NOTICE" not in row["flags"]:
                    if "RETRACTED" not in row["flags"]:
                        row["flags"].append("RETRACTED")
                    row["status"] = "PubMed: Retracted Publication" + (f"; notice: {rec['notice']}" if rec["notice"] else "")
                if doi and rec["doi"] and rec["doi"].lower() != doi.lower():
                    row["flags"].append("DOI/PMID DISAGREE")
                    row["status"] = (row["status"] + "; " if row["status"] else "") + f"PubMed gives DOI {rec['doi']} for PMID {pmid}"
                if not doi and rec["doi"]:
                    row["ident"] += f" (DOI {rec['doi']})"
                    row["doi"] = rec["doi"].lower()
        if note and row["title"]:
            nw, tw = words(note), words(row["title"])
            if len(nw) >= 3 and len(nw & tw) / len(nw) < 0.25:  # low bar: catches a DOI that points to a different paper
                row["flags"].append("TITLE MISMATCH")
                row["status"] = (row["status"] + "; " if row["status"] else "") + f"your note: “{note[:90]}”"
    except FetchError as e:
        row["flags"].append("CHECK FAILED")
        row["status"] = f"network: {e} (not a verdict; rerun)"
    if not row["flags"]:
        row["status"] = row["status"] or "resolves; no retraction found"
    row["pmid"] = pmid
    return row


def merge_rows(rows):
    """One row per paper: rows whose resolved DOI and PMID agree (or one side is empty) are merged."""
    out = []
    for r in rows:
        def agree(a, b):  # equal, or one side unknown
            return not a or not b or a == b
        same = next((o for o in out
                     if (r["doi"] and r["doi"] == o["doi"] and agree(r["pmid"], o["pmid"]))
                     or (r["pmid"] and r["pmid"] == o["pmid"] and agree(r["doi"], o["doi"]))), None)
        if same is None:
            out.append(r)
            continue
        if r["ident"] not in same["ident"]:
            same["ident"] += " = " + r["ident"]
        same["flags"] += [f for f in r["flags"] if f not in same["flags"]]
        if r["status"] and r["status"] not in same["status"]:
            same["status"] = (same["status"] + "; " if same["status"] else "") + r["status"]
        same["doi"], same["pmid"] = same["doi"] or r["doi"], same["pmid"] or r["pmid"]
        same["title"] = same["title"] or r["title"]
    for r in out:  # "ok" text must not survive next to a real flag
        if r["flags"]:
            r["status"] = "; ".join(s for s in r["status"].split("; ") if s != "resolves; no retraction found")
    return out


def parse_lines(lines):
    items, seen = [], set()
    for line in lines:
        dois = [d.rstrip(".*_:") for d in DOI_RE.findall(line)]
        pmids = PMID_RE.findall(line)
        if not dois and not pmids:
            continue
        note = DOI_RE.sub("", PMID_RE.sub("", line))
        note = re.sub(r"(https?://(dx\.)?doi\.org/)|[|*`#\-]+|\bdoi:?", " ", note, flags=re.I).strip(" .:;,")
        key = (dois[0].lower() if dois else "", pmids[0] if pmids else "")
        if key in seen:
            continue
        seen.add(key)
        items.append((dois[0] if dois else "", pmids[0] if pmids else "", note))
    return items


def dedupe_items(items):
    """Drop exact repeats, a DOI-only item when the same DOI comes with a PMID, and a PMID-only item likewise."""
    full = {(d.lower(), m) for d, m, _ in items if d and m}
    with_d, with_m = {d for d, m in full}, {m for d, m in full}
    out, seen = [], set()
    for d, m, note in items:
        key = (d.lower(), m)
        if key in seen or (d and not m and d.lower() in with_d) or (m and not d and m in with_m):
            continue
        seen.add(key)
        out.append((d, m, note))
    return out


def main():
    utf8_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--from-evidence", metavar="SESSION")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.from_evidence and not (a.file and os.path.isfile(a.file)):
        print(f"NO INPUT FILE: {a.file or '(none given)'}; give a file of DOIs or PMIDs, or --from-evidence <session folder>")
        sys.exit(2)
    if a.from_evidence:
        from _md import evidence_rows, ids_in, tables, col  # noqa: E402
        files = sorted(glob.glob(os.path.join(a.from_evidence, "evidence-*.md")))
        syn = os.path.join(a.from_evidence, "agents-synthesis.md")
        text_all = "\n".join(open(p, encoding="utf-8", errors="replace").read() for p in files)
        # 1) each evidence entry's own DOI + PMID, checked together (catches a PMID that belongs to another paper)
        pairs = []
        for eid, r in evidence_rows(text_all).items():
            d, m = sorted(r["ids"][0]), sorted(r["ids"][1])
            pairs.append((d[0] if d else "", m[0] if len(m) == 1 else "", ""))
        pairs = dedupe_items([p for p in pairs if p[0] or p[1]])
        seen_d = {p[0].lower() for p in pairs if p[0]}
        seen_m = {p[1] for p in pairs if p[1]}
        # 2) every other identifier anywhere in the evidence files (side tables, notes, drift checks) and in the synthesis
        extra_text = text_all + ("\n" + open(syn, encoding="utf-8", errors="replace").read() if os.path.exists(syn) else "")
        pmid_cols = " ".join(cells[ci] for header, body in tables(extra_text) for ci in [col(header, "pmid")] if ci is not None
                             for cells in body if ci < len(cells))
        d_all, m_all = ids_in(extra_text, pmid_cols)
        items = pairs + [(d, "", "") for d in sorted(d_all - seen_d)]
        source = f"every identifier in {', '.join(os.path.basename(f) for f in files + ([syn] if os.path.exists(syn) else [])) or 'no evidence files'}"
        rows = [check(*it) for it in items]
        covered = seen_m | {r.get("pmid") for r in rows if r.get("pmid")}
        rows += [check("", p, "") for p in sorted(m_all - covered)]
    else:
        rows = [check(*it) for it in parse_lines(open(a.file, encoding="utf-8", errors="replace").read().splitlines())]
        source = os.path.basename(a.file)
    rows = merge_rows(rows)
    n_flag = sum(1 for r in rows if r["flags"])
    kinds = {}
    for r in rows:
        for f in r["flags"]:
            kinds[f] = kinds.get(f, 0) + 1
    by_kind = (" (" + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) + ")") if kinds else ""
    out = [f"# Reference check ({cell(source)})", "",
           f"Checked {len(rows)} papers at Crossref and PubMed (DataCite/doi.org for DOIs Crossref does not know): {n_flag} flagged{by_kind}. "
           "Made by `scripts/check_refs.py`; do not edit by hand.", "",
           "| Identifier | Resolves to | Flags | Details |", "|---|---|---|---|"]
    for r in rows:
        res = f"{r['title'][:120]} ({r['journal']}, {r['year']})" if r["title"] else "-"
        out.append(f"| {cell(r['ident'])} | {cell(res)} | {cell(' · '.join(r['flags'])) or 'ok'} | {cell(r['status'])} |")
    if not rows:
        out.append("| (no DOI or PMID found in the input) | | NOTHING CHECKED | |")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
