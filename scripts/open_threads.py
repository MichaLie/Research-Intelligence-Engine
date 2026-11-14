#!/usr/bin/env python3
"""List the session's open threads, so none is dropped before you converge.

Usage: python3 scripts/open_threads.py sessions/<slug>
Writes sessions/<slug>/open-threads.md and prints its summary line.

What it does (plain language): collects, from the files, every thread the
agents opened that someone has to close:
  T-P<n>  the Deep Analyst's "Premises to check" (analyst.md, section 6)
  T-D<n>  drift-check rows in the evidence files (a method, guideline or
          resource named in your brief that has changed), unless the Librarian's
          own "matters?" cell starts with no / n/a / little / none
  T-R<n>  papers the reference checks flagged (retracted, not found, ...)
  T-Q<n>  quotes the quote check could not confirm (not found, ellipsis, joined)
A thread counts as answered when its ID (e.g. "T-P3", or a range "T-P1 to T-P4")
appears in a row of decisions.md, where the colleague records your answer
verbatim: checked (where), not relevant (why), or leave open. Unanswered
threads are listed in the handoff under "not followed up".
IDs are numbered in file order (rounds in order), so they stay the same when a
later round adds files.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import col, is_flag, rd, refcheck_rows, tables, utf8_console, write  # noqa: E402

NOT_MATTER = re.compile(r"^\W*(no\b|n/?a\b|none\b|little\b|only as before|not relevant)", re.I)
ID_RE = re.compile(r"\bT-([PDRQ])(\d+)(?:\s*(?:-|–|to)\s*(?:T-)?(?:\1)?(\d+))?", re.I)


def short(s, n=220):
    s = re.sub(r"\s+", " ", s).strip().replace("|", "/")
    return s if len(s) <= n else s[:n].rstrip() + "…"


def section(md, start):
    m = re.search(rf"^##\s*{start}.*?\n(.*?)(?=^## |\Z)", md, re.S | re.M | re.I)
    return m.group(1) if m else ""


def list_items(text):
    """Numbered or bulleted items (continuation lines joined); skips the 'Framework applied' line."""
    items, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^\s*(?:\d+[.)]|[-*•])\s+(.*)", line)
        if m:
            cur = [m.group(1)]
            items.append(cur)
        elif cur is not None and line.strip() and not line.lstrip().startswith(("|", "#")):
            cur.append(line.strip())
        elif not line.strip():
            cur = None
    return [" ".join(i) for i in items if not re.match(r"\**framework applied", " ".join(i), re.I)]


def evidence_files(s):
    def key(n):
        m = re.match(r"evidence-(for|against)(?:-r(\d+))?\.md$", n)
        return (int(m.group(2) or 1), m.group(1)) if m else (99, n)
    return sorted((n for n in os.listdir(s) if n.startswith("evidence-") and n.endswith(".md")), key=key)


def threads(s):
    """[(id, kind, text, source)] in a stable order."""
    out = []
    prem = section(rd(os.path.join(s, "analyst.md")), r"6\s*·")
    items = list_items(prem)
    if not items:  # a table instead of a list
        items = [" · ".join(c for c in cells if c) for header, body in tables(prem) for cells in body]
    out += [(f"T-P{k}", "premise to check", short(t), "analyst.md §6") for k, t in enumerate(items, 1)]
    k = 0
    for ef in evidence_files(s):
        drift = section(rd(os.path.join(s, ef)), "Drift check")
        found = False
        for header, body in tables(drift):
            found = True
            ci = col(header, "matter")
            for cells in body:
                verdict = cells[ci] if ci is not None and ci < len(cells) else ""
                if verdict and NOT_MATTER.match(verdict.replace("*", "")):
                    continue
                k += 1
                out.append((f"T-D{k}", "drift (changed since your brief)", short(cells[0] + (" → matters? " + verdict if verdict else "")), ef))
        if not found:
            for t in list_items(drift):
                k += 1
                out.append((f"T-D{k}", "drift (changed since your brief)", short(t), ef))
    k = 0
    for fname, ident, res, flags, _ in refcheck_rows(s):
        if is_flag(flags):
            k += 1
            out.append((f"T-R{k}", "flagged reference", short(f"{flags}: {ident} ({res[:90]})"), fname))
    k = 0
    for header, body in tables(rd(os.path.join(s, "quotecheck.md"))):
        ci = col(header, "result")
        if ci is None:
            continue
        for cells in body:
            if ci < len(cells) and cells[ci].startswith(("NOT FOUND", "ELLIPSIS", "JOINED")):
                k += 1
                out.append((f"T-Q{k}", "quote to look at", short(f"{cells[0]}: {cells[ci]} ({cells[3][:80]})"), "quotecheck.md"))
    return out


def answers(s):
    """thread id -> (decisions.md row number, the choice cell), from rows that name the ID."""
    got = {}
    for header, body in tables(rd(os.path.join(s, "decisions.md"))):
        ci = col(header, "your choice")
        for n, cells in enumerate(body, 1):
            text = " ".join(cells)
            for kind, a, b in ID_RE.findall(text):
                for i in range(int(a), int(b or a) + 1):
                    got.setdefault(f"T-{kind.upper()}{i}", (cells[0] or str(n), cells[ci] if ci is not None and ci < len(cells) else ""))
    return got


def main():
    utf8_console()
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
            print(f"NO SUCH SESSION FOLDER: {sys.argv[1]}")
        sys.exit(2)
    s = sys.argv[1].rstrip("/")
    th, ans = threads(s), answers(s)
    n_open = sum(1 for t in th if t[0] not in ans)
    summary = (f"{len(th)} threads: {len(th) - n_open} answered in decisions.md, {n_open} open "
               f"({sum(1 for t in th if t[0].startswith('T-P'))} premises, {sum(1 for t in th if t[0].startswith('T-D'))} drift rows, "
               f"{sum(1 for t in th if t[0].startswith('T-R'))} flagged references, {sum(1 for t in th if t[0].startswith('T-Q'))} quotes).")
    out = ["# Open threads", "", summary + " Made by `scripts/open_threads.py`; do not edit by hand. "
           "Answers go in decisions.md, with the thread ID, in your words.", "",
           "| ID | Kind | Thread (agent or script text, shortened) | From | Answered |", "|---|---|---|---|---|"]
    for tid, kind, text, src in th:
        a = ans.get(tid)
        out.append(f"| {tid} | {kind} | {text} | {src} | {('decisions.md #' + a[0] + ': ' + short(a[1], 60)) if a else 'open'} |")
    if not th:
        out.append("| - | | no threads found (no analyst.md §6, drift check, flagged reference or quote problem yet) | | |")
    write(os.path.join(s, "open-threads.md"), "\n".join(out) + "\n")
    print(summary)
    print(f"WROTE {os.path.join(s, 'open-threads.md')}")


if __name__ == "__main__":
    main()
