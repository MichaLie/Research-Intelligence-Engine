#!/usr/bin/env python3
"""Assemble a handoff for the researcher's second reader or a team meeting.

Usage: python3 scripts/handoff.py sessions/<slug>

What it does: copies, without rewording, the researcher's question and expectation
(from brief.md), their argument (argument.md), the sources the argument cites
(rows copied from the evidence files), the Fresh-eyes counts, the quote check,
each flagged reference once (grouped by flag), the open threads nobody closed,
what the Librarians did not search, and the Critic's last open questions into
handoff.md, and adds the researcher's own two questions for their second reader
(second-reader-questions.md). The second reader is whoever checks the work: a
supervisor, a team expert, a senior researcher or a co-author, as the researcher
named them in second-reader.md at the start. Last comes a list of facts about
how AI was used in the session (dates, roles, searches, checks), for a methods
section, a thesis declaration or a funder's AI-use statement;
the researcher edits it before using it.
Nothing in it is written by an agent except what is quoted and labelled.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import col, is_flag, latest_fresh_eyes, rd, refcheck_rows, tables, utf8_console, verdict_counts, write  # noqa: E402
from open_threads import answers, threads  # noqa: E402

QUESTION_FILES = ("second-reader-questions.md", "supervisor-questions.md")  # AGENTS.md §9 step 0; the second name is read only for sessions made before the rename
READER_FILE = "second-reader.md"  # AGENTS.md §0 step 4, the researcher's own words
NOBODY = re.compile(r"^\s*\(?\s*(nobody|no one|none|no|skip|skipped|not named|n/a|-)\s*\)?\s*\.?\s*$", re.I)


def section(md, number):
    m = re.search(rf"^## {number} ·.*?\n(.*?)(?=^## |\Z)", md, re.S | re.M)
    return (m.group(1).strip() if m else "").strip() or "(not written)"


def named_section(md, name):
    m = re.search(rf"^## {name}.*?\n(.*?)(?=^## |\Z)", md, re.S | re.M | re.I)
    return m.group(1).strip() if m else ""


def drop_heading(text):
    return re.sub(r"^\s*#[^\n]*\n", "", text, count=1).strip()


def cut(text, n, where):
    return text if len(text) <= n else text[:n].rstrip() + f" … (cut here; the rest is in {where})"


def main():
    utf8_console()
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        sys.exit(2)
    s = sys.argv[1].rstrip("/")
    P = lambda n: os.path.join(s, n)
    brief, arg = rd(P("brief.md")), rd(P("argument.md"))
    fe_path = latest_fresh_eyes(s)
    counts = verdict_counts(rd(fe_path))
    seals = json.loads(rd(P("seals.json")) or "{}")
    ev_files = sorted(glob.glob(P("evidence-*.md")))

    # sources the argument cites, rows copied from the evidence tables
    tl = set(rd(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "argument.md")).splitlines())
    cited = set(re.findall(r"\bE-[FA]\d+\b", "\n".join(l for l in arg.splitlines() if l not in tl)))
    src = {}
    for ef in ev_files:
        for header, body in tables(rd(ef)):
            ci_c, ci_i, ci_r = col(header, "citation"), col(header, "doi", "pmid", "identifier"), col(header, "read as")
            if ci_r is None:
                continue
            for cells in body:
                m = re.search(r"\bE-[FA]\d+\b", cells[0] if cells else "")
                if m and m.group(0) in cited and m.group(0) not in src:
                    get = lambda i: cells[i] if i is not None and i < len(cells) else ""
                    src[m.group(0)] = f"| {m.group(0)} | {get(ci_c)} | {get(ci_i)} | {get(ci_r)} | {os.path.basename(ef)} |"
    key = lambda e: (e[2], int(re.sub(r"\D", "", e)))
    src_rows = [src[e] for e in sorted(src, key=key)] + [f"| {e} | (not found in any evidence file) | | | |" for e in sorted(cited - set(src), key=key)]
    src_md = ("| ID | Citation | DOI / PMID | Read as | From |\n|---|---|---|---|---|\n" + "\n".join(src_rows)) if src_rows else "(the argument cites no evidence IDs)"

    # reference flags: each paper once, grouped by flag
    groups = {}
    for fname, ident, res, flags, _ in refcheck_rows(s):
        if is_flag(flags):
            groups.setdefault(flags, []).append(f"  - {ident} ({res[:90]}) [{fname}]")
    flags_md = "\n".join(f"- **{k}** ({len(v)}):\n" + "\n".join(v) for k, v in sorted(groups.items())) if groups else (
        "- none found by the checks that ran" if glob.glob(P("refcheck-*.md")) else "- no reference check has run")
    qc = rd(P("quotecheck.md"))
    qc_line = next((l for l in qc.splitlines() if l.startswith("Checked ")), "") or "no quote check has run"

    # open threads not answered
    th, ans = threads(s), answers(s)
    open_th = [t for t in th if t[0] not in ans]
    threads_md = (f"{len(th)} threads, {len(th) - len(open_th)} answered in decisions.md. Not followed up:\n"
                  + ("\n".join(f"- {t[0]} ({t[1]}, {t[3]}): {t[2]}" for t in open_th) or "- none")) if th else "(no open-thread list: open_threads.py found nothing)"

    # what the Librarians did not search (their last report per stance)
    not_searched = []
    for stance in ("for", "against"):
        fs = sorted((f for f in ev_files if re.match(rf"evidence-{stance}(-r\d+)?\.md$", os.path.basename(f))),
                    key=lambda f: int((re.search(r"-r(\d+)\.md$", f) or [0, 1])[1]))
        if fs:
            txt = named_section(rd(fs[-1]), "What I did not search")
            not_searched.append(f"*{os.path.basename(fs[-1])} (Librarian, agent text):*\n{cut(txt, 1200, os.path.basename(fs[-1])) or '(section empty)'}")

    critics = sorted(glob.glob(P("critic-round-*.md")), key=lambda f: int(re.sub(r"\D", "", os.path.basename(f)) or 0))
    qs = "(no Critic report)"
    if critics:
        last = rd(critics[-1])
        m = re.search(r"(?ims)^## 7 ·.*?\n(.*?)(?=^## |\Z)", last) or re.search(r"(?is)(?:three )?questions for (?:the researcher|the student|you).*?\n(.*)$", last)
        qs = (m.group(1).strip() if m else "(section not found)")[:1500]
    arg_body = drop_heading(arg) or "(not written)"
    reader = re.sub(r"\s+", " ", drop_heading(rd(P(READER_FILE))))[:200]
    named = bool(reader) and not NOBODY.match(reader)
    reader_line = (f"For your second reader, named in your words as: {reader}. It works for a team meeting too." if named
                   else "For whoever checks your work (a supervisor, a team expert, a senior researcher or a co-author) or a team meeting.")
    mine = next((drop_heading(rd(P(n))) for n in QUESTION_FILES if drop_heading(rd(P(n)))), "") or "1.\n2."
    n_arg = len(seals.get("argument.md", []))

    # how AI was used: facts from the files only
    def dates(name):
        e = seals.get(name) or []
        return e[0]["sealed_at"][:10] if e else ""
    dbs = {}
    for ef in ev_files:
        for header, body in tables(named_section(rd(ef), "Query log")):
            ci = col(header, "database")
            for cells in body:
                db = (cells[ci].strip().lower() if ci is not None and ci < len(cells) else "") or "database not recorded"
                dbs[db] = dbs.get(db, 0) + 1
    n_searches = sum(dbs.values())
    ran = [label for label, pat in (("Deep Analyst", "analyst.md"), ("Librarians", "evidence-*.md"), ("Critic", "critic-round-*.md"),
                                    ("Fresh eyes", "fresh-eyes*.md"), ("Deep Analyst synthesis", "agents-synthesis.md")) if glob.glob(P(pat))]
    rc_lines = [next((l for l in rd(f).splitlines() if l.startswith("Checked ")), "") for f in glob.glob(P("refcheck-*.md"))]
    ai_md = "\n".join([
        f"- Session folder: {os.path.basename(s)}; brief sealed {dates('brief.md') or '(not sealed)'}; argument sealed {n_arg} time(s)"
        + (f", last {seals['argument.md'][-1]['sealed_at'][:10]}" if n_arg else "") + ".",
        f"- Agent roles that produced files: {', '.join(ran) or 'none'} (run by the AI coding agent; the researcher wrote brief.md, argument.md and their decisions).",
        f"- Literature searches logged by the Librarians: {n_searches}" + (f" ({', '.join(f'{k}: {v}' for k, v in sorted(dbs.items()))}; from the evidence files' query logs)." if dbs else "."),
        f"- Reference checks (scripts/check_refs.py; Crossref, PubMed, DataCite, doi.org): {len(rc_lines)} run(s). Quote check: {qc_line.split(' Made by')[0]}",
        f"- Fresh eyes (separate agent) checked: {os.path.basename(fe_path) or 'not run'}.",
        "- argument.md was written by the researcher and sealed with scripts/seal.py; the dashboard lists any sentence in it that repeats agent text word for word.",
        "- AI tool and model: [fill in].",
    ])

    out = f"""# Handoff: {os.path.basename(s)}

*{reader_line} Assembled by `scripts/handoff.py` from your files; nothing reworded.*

## The question (your words)
{section(brief, 1)}

## What you expected at the start
{section(brief, 2)}

## Your argument now
{arg_body}

## Sources your argument cites (copied from the evidence files)
{src_md}

## Checks
- Fresh eyes ({os.path.basename(fe_path) or 'not run'}; argument sealed {n_arg} time(s)): {counts['VERIFIED']} verified · {counts['UNVERIFIED']} unverified · {counts['CONTRADICTED']} contradicted
- Quote check: {qc_line.split(' Made by')[0]}
- Reference flags, each paper once:
{flags_md}

## Not followed up (open threads)
{threads_md}

## What the Librarians did not search
{chr(10).join(not_searched) or '(no evidence files)'}

## Open questions the Critic left (agent text, last round)
{qs}

## Your questions for your second reader (your words)
{mine}

## How AI was used in this session (facts from your files; edit before using)
{ai_md}
"""
    write(P("handoff.md"), out)
    print(f"WROTE {P('handoff.md')}")


if __name__ == "__main__":
    main()
