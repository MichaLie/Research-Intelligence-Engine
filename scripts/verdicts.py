#!/usr/bin/env python3
"""Print Fresh eyes' verdicts for relaying, verbatim, with the evidence rows they point to.

Usage: python3 scripts/verdicts.py sessions/<slug> [fresh-eyes-v<k>.md]
(default: the newest fresh-eyes-v<k>.md)

What it does (plain language): the colleague shows the researcher Fresh eyes'
verdicts without retelling them. This script prints the report's own counts,
then every UNVERIFIED and CONTRADICTED row exactly as Fresh eyes wrote it, and
under each the evidence-table rows (ID, citation, DOI / PMID, read as, quote)
for the evidence IDs that row names, plus the quote check's result for them.
The colleague pastes this output; it does not open papers, search, or judge a
verdict itself. A disputed verdict goes back to Fresh eyes, not to the colleague.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import col, latest_fresh_eyes, rd, tables, utf8_console, verdict_counts  # noqa: E402


def main():
    utf8_console()
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(2)
    s = sys.argv[1].rstrip("/")
    fe = os.path.join(s, sys.argv[2]) if len(sys.argv) == 3 else latest_fresh_eyes(s)
    text = rd(fe)
    if not text.strip():
        print(f"NO FRESH-EYES REPORT {fe or '(none in ' + s + ')'}: nothing to relay")
        sys.exit(1)
    ev = {}
    for ef in sorted(glob.glob(os.path.join(s, "evidence-*.md"))):
        for header, body in tables(rd(ef)):
            idx = [col(header, n) for n in ("citation", "doi", "read as", "quote")]
            if idx[2] is None:
                continue
            for cells in body:
                m = re.search(r"\bE-[FA]\d+\b", cells[0] if cells else "")
                if m and m.group(0) not in ev:
                    ev[m.group(0)] = " | ".join([m.group(0)] + [cells[i] if i is not None and i < len(cells) else "" for i in idx]) + f" ({os.path.basename(ef)})"
    qc = {}
    for header, body in tables(rd(os.path.join(s, "quotecheck.md"))):
        ci = col(header, "result")
        if ci is not None:
            for cells in body:
                if ci < len(cells) and cells[ci] != "FOUND":
                    qc.setdefault(cells[0], []).append(cells[ci])
    c = verdict_counts(text)
    print(f"FROM {os.path.basename(fe)} (Fresh eyes' own words; relay verbatim)")
    print(f"Counts from its table: {c['VERIFIED']} verified · {c['UNVERIFIED']} unverified · {c['CONTRADICTED']} contradicted")
    summ = re.search(r"^## Summary\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if summ:
        print("\nIts summary:\n" + summ.group(1).strip())
    for header, body in tables(text):
        ci = col(header, "verdict")
        if ci is None:
            continue
        print("\n| " + " | ".join(header) + " |")
        for cells in body:
            v = cells[ci].upper() if ci < len(cells) else ""
            if not re.match(r"\W*(UNVERIFIED|CONTRADICTED)", v):
                continue
            print("| " + " | ".join(cells) + " |")
            for eid in sorted(set(re.findall(r"\bE-[FA]\d+\b", " ".join(cells)))):
                print(f"    evidence: {ev.get(eid, eid + ' (not in the evidence files)')}")
                if eid in qc:
                    print(f"    quote check: {', '.join(qc[eid])}")


if __name__ == "__main__":
    main()
