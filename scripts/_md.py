"""Shared reading of the session's markdown tables, so every script counts the same way.

What it does (plain language): finds the tables in a markdown file, knows which
column is which by its header ("Verdict", "Read as", "DOI / PMID"), and pulls
identifiers out of the right places. v2.0's first test showed three scripts
counting the same Fresh-eyes table three ways; this module is the one way.
"""
import re

DOI_RE = re.compile(r"\b(10\.\d{4,9}/(?:[^\s|,;\]>\"'`*()]|\([^\s()]*\))+)", re.I)  # allows balanced (...) inside a DOI
PMID_TAG_RE = re.compile(r"\bPMID[:\s]*?(\d{1,9})\b", re.I)
BARE_NUM_RE = re.compile(r"(?<![\d.])(\d{6,9})(?![\d.])")
VERDICTS = ("VERIFIED", "UNVERIFIED", "CONTRADICTED")


def utf8_console():
    """Print UTF-8 whatever the console's code page (Windows cp1250/cp1252 would crash on '·', 'α', '→')."""
    import sys
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def rd(path):
    """A session file's text, or '' if it does not exist. Always UTF-8."""
    import os
    if not path or not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text, mode="w"):
    with open(path, mode, encoding="utf-8") as f:
        f.write(text)


def tables(text):
    """Return [(header_cells, [row_cells, ...]), ...] for every markdown table."""
    out, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            cur = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cur is None:
            cur = (cells, [])
            out.append(cur)
        elif all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        else:
            cur[1].append(cells)
    return out


def col(header, *names):
    for i, h in enumerate(header):
        hl = h.lower()
        if any(n in hl for n in names):
            return i
    return None


def clean_doi(d):
    return d.rstrip(".*_:").lower()


def ids_in(text, pmid_column_text=""):
    """DOIs anywhere, PMIDs written as 'PMID 123', and bare numbers in a PMID column.
    Digits inside a DOI are never read as a PMID: DOIs are removed before PMIDs are looked for."""
    dois = {clean_doi(d) for d in DOI_RE.findall(text)}
    no_doi = DOI_RE.sub(" ", text)
    pmids = set(PMID_TAG_RE.findall(no_doi)) | set(BARE_NUM_RE.findall(DOI_RE.sub(" ", pmid_column_text)))
    pmids -= set(re.findall(r"\bPMC(\d+)", text, re.I))  # a PMCID's digits are not a PMID
    return dois, pmids


def agreement(decisions_text):
    """(agreed, counted) from the 'Same as the colleague's view?' column; only yes/no cells count."""
    agreed = counted = 0
    for header, body in tables(decisions_text):
        ci = col(header, "same")
        if ci is None:
            continue
        for cells in body:
            v = cells[ci].strip().lower().strip("*_ ") if ci < len(cells) else ""
            if v.startswith(("yes", "no")):
                counted += 1
                agreed += v.startswith("yes")
    return agreed, counted


def evidence_rows(text):
    """Map evidence ID -> {'row': full row text, 'ids': (dois, pmids) from the identifier column only, 'read_as': ...}."""
    rows = {}
    for header, body in tables(text):
        ci_id = col(header, "doi", "pmid", "identifier")
        ci_read = col(header, "read as")
        for cells in body:
            first = cells[0] if cells else ""
            m = re.search(r"\bE-[FA]\d+\b", first)
            if not m:
                continue
            idcell = cells[ci_id] if ci_id is not None and ci_id < len(cells) else ""
            if idcell:
                dois, pmids = ids_in(idcell, idcell)
            else:
                dois, pmids = ids_in(" ".join(cells))
                dois, pmids = set(list(dois)[:1]), set(list(pmids)[:1])
            read = cells[ci_read].lower() if ci_read is not None and ci_read < len(cells) else ""
            rows[m.group(0)] = {"row": " | ".join(cells), "ids": (dois, pmids), "read_as": read}
    return rows


def verdict_counts(text):
    """Count verdicts in the Verdict column of Fresh-eyes tables (first word of the cell)."""
    counts = {v: 0 for v in VERDICTS}
    for header, body in tables(text):
        ci = col(header, "verdict")
        if ci is None:
            continue
        for cells in body:
            if ci < len(cells):
                w = re.sub(r"[^A-Z]", " ", cells[ci].upper()).split()
                if w and w[0] in counts:
                    counts[w[0]] += 1
    return counts


def read_as_counts(rows):
    c = {"full text": 0, "abstract only": 0, "no access": 0, "other": 0}
    for r in rows.values():
        ra = r["read_as"].replace("-", " ")
        hits = [(ra.find(p), k) for p, k in (("full text", "full text"), ("abstract", "abstract only"), ("no access", "no access")) if p in ra]
        c[min(hits)[1] if hits else "other"] += 1  # the label written first in the cell wins
    return c


def latest_fresh_eyes(session):
    """Path of the newest Fresh-eyes report (fresh-eyes-v<k>.md, highest k), or fresh-eyes.md, or ''."""
    import glob
    import os
    vs = sorted(glob.glob(os.path.join(session, "fresh-eyes-v*.md")),
                key=lambda p: int(re.search(r"-v(\d+)\.md$", p).group(1)) if re.search(r"-v(\d+)\.md$", p) else 0)
    if vs:
        return vs[-1]
    p = os.path.join(session, "fresh-eyes.md")
    return p if os.path.exists(p) else ""


def refcheck_files(session):
    """Reference-check files in a stable order: your own list, then each round, then the synthesis, then any other."""
    import glob
    import os

    def key(p):
        n = os.path.basename(p)
        m = re.search(r"-r(\d+)\.md$", n)
        return (0 if "mine" in n else 1 if m or n == "refcheck-evidence.md" else 2 if "synthesis" in n else 3,
                int(m.group(1)) if m else 0, n)
    return sorted(glob.glob(os.path.join(session, "refcheck-*.md")), key=key)


def refcheck_rows(session, only=None):
    """Every checked paper once (deduplicated by DOI/PMID across all refcheck files):
    [(file name, identifier cell, resolves-to cell, flags cell, ids)], ids = set of lower-case DOIs and PMIDs."""
    import os
    out, seen = [], set()
    for rf in refcheck_files(session):
        if only and not only(os.path.basename(rf)):
            continue
        for header, body in tables(rd(rf)):
            if not header or "Identifier" not in header[0]:
                continue
            for cells in body:
                if len(cells) < 3:
                    continue
                d, m = ids_in(cells[0], cells[0])
                ids = d | m or {cells[0].lower()}
                if ids & seen:
                    continue
                seen |= ids
                out.append((os.path.basename(rf), cells[0], cells[1], cells[2], ids))
    return out


def is_flag(flags_cell):
    return flags_cell.strip().lower() not in ("ok", "")
