#!/usr/bin/env python3
"""Build the session dashboard from the files, with a gap check ("Needs a look").

Usage: python3 scripts/dashboard.py sessions/<slug>

What it does: reads the session's files (never the conversation) and writes
dashboard.html. The agent does not write the dashboard; this script does, so
the page shows what is on disk, including what is missing. The gap check
looks for: agent output that appeared before the researcher's brief was sealed;
the researcher's files changed after sealing; evidence without a reference check;
retracted or unresolved sources cited; an argument without a Fresh-eyes
report; decisions without a reason; fewer than two rounds before converging;
quotes the quote check could not confirm; open threads with no recorded answer.
Gaps are red (something went wrong) or amber (worth a look). Silence is never
shown as fine: a check that could not run says so.

Limits: file times come from the file system. "Before the seal" uses a file's
creation time where the system records one (macOS, Windows) and its last change
elsewhere, so on Linux a file created before the seal and edited after it looks "after". The gap check is a flag for a person
to look at, not proof.
"""
import datetime as dt
import glob
import hashlib
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import agreement, col, evidence_rows, ids_in, is_flag, latest_fresh_eyes, rd, read_as_counts, refcheck_rows, tables, utf8_console, verdict_counts, write  # noqa: E402
from open_threads import answers, threads  # noqa: E402

MODE_GLOSS = {"you-first": "you-first (you write before any agent shows you anything)",
              "agents-first": "agents-first (comparison mode: the agents went first)"}
YOURS = ["brief.md", "reading-notes.md", "argument.md", "reflection.md"]
AGENT_GLOBS = ["analyst.md", "evidence-*.md", "critic-round-*.md", "fresh-eyes*.md", "agents-synthesis.md"]
WHO = {"brief.md": "you", "reading-notes.md": "you", "argument.md": "you", "reflection.md": "you",
       "analyst.md": "Deep Analyst", "evidence-for.md": "Librarian (for)", "evidence-against.md": "Librarian (against)",
       "fresh-eyes.md": "Fresh eyes", "weakest-point.md": "you", "versions": "script", "agents-synthesis.md": "Deep Analyst (synthesis)",
       "refcheck-mine.md": "script", "quotecheck.md": "script", "open-threads.md": "script", "second-reader.md": "you", "second-reader-questions.md": "you", "supervisor-questions.md": "you (older sessions)", "fresh-eyes-synthesis.md": "Fresh eyes (on the agents' synthesis)", "handoff.md": "script + you",
       "status.md": "colleague", "decisions.md": "you (choices and reasons)", "colleague-views.md": "colleague (after your choice)", "my-papers.txt": "colleague (from your brief)"}


def ftime(p):
    """When the file first appeared (creation time where recorded); for "before the seal"."""
    st = os.stat(p)
    t = min(getattr(st, "st_birthtime", st.st_mtime), st.st_mtime)
    return dt.datetime.fromtimestamp(t, dt.timezone.utc)


def mtime(p):
    """Last change; for "changed after"."""
    return dt.datetime.fromtimestamp(os.stat(p).st_mtime, dt.timezone.utc)


def local(t):
    return t.astimezone().strftime("%Y-%m-%d %H:%M")


def table_rows(text):
    rows = [r for r in text.splitlines() if r.strip().startswith("|")]
    out = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        out.append(cells)
    return out


def main():
    utf8_console()
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        sys.exit(2)
    sess = sys.argv[1].rstrip("/")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = lambda n: os.path.join(sess, n)
    status = dict(re.findall(r"^- \*\*(.+?):\*\*\s*(.*)$", rd(P("status.md")), re.M))
    mode = status.get("Mode", "you-first").lower()
    seals = json.loads(rd(P("seals.json")) or "{}")
    gaps = []  # (level, text)

    def sealed_at(name):
        e = seals.get(name)
        return dt.datetime.strptime(e[-1]["sealed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc) if e else None

    def first_seal(name):
        e = seals.get(name)
        return dt.datetime.strptime(e[0]["sealed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc) if e else None

    # 1. brief sealed, unchanged, and before any agent output
    bseal = first_seal("brief.md")
    tpl = rd(os.path.join(root, "templates", "brief.md"))
    if not os.path.exists(P("brief.md")) or rd(P("brief.md")).strip() == tpl.strip():
        gaps.append(("amber", "Your brief is not written yet."))
    elif not bseal:
        gaps.append(("red" if any(glob.glob(P(g)) for g in AGENT_GLOBS) else "amber", "Your brief is not sealed."))
    agent_files = sorted({f for g in AGENT_GLOBS for f in glob.glob(P(g))})
    if bseal and "agents-first" not in mode:
        early = [os.path.basename(f) for f in agent_files if ftime(f) < bseal]
        if early:
            gaps.append(("red", "Agent output dated before your brief was sealed: " + ", ".join(early) + "."))
    for name, entries in seals.items():
        if os.path.exists(P(name)) and hashlib.sha256(open(P(name), "rb").read()).hexdigest() != entries[-1]["sha256"]:
            gaps.append(("red", f"{name} changed after it was sealed (re-seal it if you revised it)."))

    # 2. references
    ev_text = "\n".join(rd(f) for f in sorted(glob.glob(P("evidence-*.md"))))
    ev = evidence_rows(ev_text)
    ev_ids = {k: v["row"] for k, v in ev.items()}
    flagged = {}  # identifier -> flags (each paper once across refcheck files)
    ref_rows = []
    for fname, ident, res, fl, ids in refcheck_rows(sess):
        ref_rows.append((fname, [ident, res, fl]))
        if is_flag(fl):
            for i in ids:
                flagged[i] = fl
    mine_flagged = [r for f, r in ref_rows if "mine" in os.path.basename(f) and is_flag(r[2])]
    if mine_flagged:
        gaps.append(("amber", f"{len(mine_flagged)} of your own papers flagged by the reference check ("
                              + "; ".join(f"{r[0]}: {r[2]}" for r in mine_flagged[:5]) + "); see refcheck-mine.md."))
    rc_ev = sorted(glob.glob(P("refcheck-evidence*.md")), key=mtime)
    newest_ev = max((mtime(f) for f in glob.glob(P("evidence-*.md"))), default=None)
    if ev_ids and not rc_ev:
        gaps.append(("red", "Evidence files exist but their references have not been checked (no refcheck-evidence-r<N>.md yet)."))
    elif ev_ids and mtime(rc_ev[-1]) < newest_ev:
        gaps.append(("amber", "The evidence files changed after the last reference check; rerun check_refs.py."))
    qc_text = rd(P("quotecheck.md"))
    qc_bad = {}
    for header, body in tables(qc_text):
        ci = col(header, "result")
        if ci is not None:
            for c in body:
                if ci < len(c) and c[ci].startswith(("NOT FOUND", "ELLIPSIS", "JOINED")):
                    qc_bad.setdefault(c[0], c[ci])
    if ev_ids and not qc_text:
        gaps.append(("amber", "The quotes in the evidence files have not been checked against the saved full texts (run check_quotes.py)."))
    elif ev_ids and mtime(P("quotecheck.md")) < newest_ev:
        gaps.append(("amber", "The evidence files changed after the quote check; rerun check_quotes.py."))
    if qc_bad:
        gaps.append(("amber", f"{len(qc_bad)} evidence entr{'y has a quote' if len(qc_bad) == 1 else 'ies have quotes'} the quote check could not confirm as quoted ({', '.join(sorted(qc_bad))}); see quotecheck.md."))
    for name in ("argument.md", "agents-synthesis.md"):
        tlines = set(rd(os.path.join(root, "templates", name)).splitlines())
        txt = "\n".join(line for line in rd(P(name)).splitlines() if line not in tlines)
        for eid in sorted(set(re.findall(r"\bE-[FA]\d+\b", txt))):
            if eid not in ev_ids:
                gaps.append(("red", f"{name} cites {eid}, which is not in the evidence files."))
                continue
            own_dois, own_pmids = ev[eid]["ids"]
            for fl in sorted({fl for ident, fl in flagged.items() if ident in own_dois or ident in own_pmids}):
                lvl = "red" if ("RETRACTED" in fl or "NOT FOUND" in fl) else "amber"  # citing a retraction notice itself is fine
                gaps.append((lvl, f"{name} cites {eid}, whose reference is flagged: {fl}."))
    if os.path.exists(P("my-papers.txt")) and rd(P("my-papers.txt")).strip() and not os.path.exists(P("refcheck-mine.md")):
        gaps.append(("red", "Your own papers were listed but not checked (refcheck-mine.md missing)."))

    # 3. decisions, rounds, argument, fresh eyes
    for header, body in tables(rd(P("decisions.md"))):
        ci_c, ci_r = col(header, "your choice"), col(header, "your reason")
        if ci_c is None:
            continue
        for c in body:
            get = lambda i: c[i].strip() if i is not None and i < len(c) else ""
            if get(ci_c) and not get(ci_r):
                gaps.append(("amber", f"Decision {c[0]} has no reason recorded."))
    agree, n_same = agreement(rd(P("decisions.md")))
    if "would have chosen" in rd(P("decisions.md")).lower():
        gaps.append(("red", "decisions.md contains the colleague's own view; it belongs in colleague-views.md, because the roles read decisions.md."))
    # checkpoints: fixed option order, both columns filled, no recommendation words
    order = ["continue", "deep dive", "converge", "redirect", "stop"]
    for cp in sorted(glob.glob(P("checkpoint-*.md"))):
        for header, body in tables(rd(cp)):
            if col(header, "buys") is None:
                continue
            labels = [c[0].lower() for c in body]
            seen = [next((o for o in order if o in l), "?") for l in labels]
            if [s for s in seen if s != "?"] != [o for o in order if o in seen]:
                gaps.append(("amber", f"{os.path.basename(cp)}: options are not in the template's fixed order."))
            for c in body:
                if len(c) < 3 or not c[1].strip() or not c[2].strip():
                    gaps.append(("amber", f"{os.path.basename(cp)}: option \u201c{c[0][:40]}\u201d lacks what it buys or what it risks."))
        if re.search(r"\b(I recommend|we recommend|best option|the right choice|I suggest)\b", rd(cp), re.I):
            gaps.append(("red", f"{os.path.basename(cp)} contains recommending language."))
    rounds = len(glob.glob(P("critic-round-*.md")))
    if "converge" in (status.get("Stop reason", "") + status.get("Step", "")).lower() and rounds < 2:
        gaps.append(("amber", f"Converged after {rounds} round(s); the minimum is 2."))
    # rounds: which Librarian stances searched in which round (from file names)
    rounds_seen = {}
    for f in glob.glob(P("evidence-*.md")):
        m = re.match(r"evidence-(for|against)(?:-r(\d+))?\.md$", os.path.basename(f))
        if m:
            rounds_seen.setdefault(int(m.group(2) or 1), []).append(m.group(1).upper())
    round_line = " · ".join(f"round {r}: {' + '.join(sorted(s))}" for r, s in sorted(rounds_seen.items())) or "no searches yet"
    # verbatim overlap: argument sentences that match agent-written files (8+ words in a row)
    def grams(text, n=8):
        w = re.findall(r"[a-z0-9]+", text.lower())
        return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}
    # each sealed version of the argument vs agent text that existed before that seal,
    # minus the researcher's own phrases (brief, notes, decisions, earlier versions), since agents quote them
    tl = set(rd(os.path.join(root, "templates", "argument.md")).splitlines())
    own = " ".join(rd(P(n)) for n in ("brief.md", "reading-notes.md", "decisions.md", "my-papers.txt"))
    copied = []
    for k, entry in enumerate(seals.get("argument.md", []), 1):
        vf = os.path.join(sess, "versions", f"argument-v{k}.md")
        if os.path.exists(vf):
            text_k = rd(vf)
        elif k == len(seals["argument.md"]):
            text_k = rd(P("argument.md"))
        else:
            continue
        t_k = dt.datetime.strptime(entry["sealed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        before = [f for g in AGENT_GLOBS + ["checkpoint-*.md", "colleague-views.md"] for f in glob.glob(P(g)) if ftime(f) < t_k]
        ag = grams(" ".join(rd(f) for f in before)) - grams(own)
        for s in re.split(r"(?<=[.!?])\s+", " ".join(l for l in text_k.splitlines() if l not in tl)):
            if len(s.split()) >= 8 and grams(s) & ag and s not in copied:
                copied.append(s)
        own += " " + text_k
    if copied:
        gaps.append(("amber", f"{len(copied)} sentence(s) in your sealed argument repeat agent-written text word for word (8+ words), e.g. \u201c{copied[0][:80]}\u2026\u201d. Are they yours?"))
    arg_txt = rd(P("argument.md"))
    arg_written = arg_txt.strip() and arg_txt.strip() != rd(os.path.join(root, "templates", "argument.md")).strip()
    if arg_written and not sealed_at("argument.md"):
        gaps.append(("amber", "Your argument is written but not sealed."))
    fe_path = latest_fresh_eyes(sess)
    if sealed_at("argument.md"):
        n_seals = len(seals["argument.md"])
        if not fe_path:
            gaps.append(("red", "Your argument has not been checked by Fresh eyes yet."))
        elif not os.path.exists(P(f"fresh-eyes-v{n_seals}.md")) and ftime(fe_path) < sealed_at("argument.md"):
            gaps.append(("red", f"Fresh eyes checked an earlier version of your argument (latest report: {os.path.basename(fe_path)}; argument seal #{n_seals})."))
    step = (status.get("Step", "") + " " + status.get("Stop reason", "")).lower()
    # the synthesis is written during the close, so its absence is a gap only once the handoff exists
    if any(w in step for w in ("close", "closed", "complete", "9 ·")) and os.path.exists(P("handoff.md")) and not os.path.exists(P("agents-synthesis.md")):
        gaps.append(("red", "The session is closing but the agents' synthesis (agents-synthesis.md) is missing: the comparison step did not happen."))
    if os.path.exists(P("agents-synthesis.md")):
        fs = rd(P("fresh-eyes-synthesis.md"))
        if not fs.strip():
            gaps.append(("amber", "The agents' synthesis has not been checked by Fresh eyes yet (fresh-eyes-synthesis.md missing)."))
        else:
            sc = verdict_counts(fs)
            if sc["CONTRADICTED"] or sc["UNVERIFIED"]:
                gaps.append(("amber", f"In the agents' own synthesis, Fresh eyes marked {sc['CONTRADICTED']} claim(s) contradicted and {sc['UNVERIFIED']} unverified (fresh-eyes-synthesis.md)."))
    fe = rd(fe_path) if fe_path else ""
    counts = verdict_counts(fe)
    if counts["CONTRADICTED"] and "contradict" not in rd(P("decisions.md")).lower():
        gaps.append(("amber", f"Fresh eyes found {counts['CONTRADICTED']} contradicted claim(s); no resolution recorded in decisions.md yet."))
    # open threads: premises, drift rows, flagged references, quotes; answered = named in decisions.md
    th, ans = threads(sess), answers(sess)
    n_open = sum(1 for t in th if t[0] not in ans)
    converging = arg_written or any(w in step for w in ("converge", "7 ·", "close", "9 ·"))
    if n_open and converging:
        gaps.append(("amber", f"{n_open} open thread(s) have no recorded answer (premises to check, drift rows, flagged references, quotes); "
                              "run open_threads.py and take open-threads.md to the researcher before the argument is final."))
    for eid in sorted(set(re.findall(r"\bE-[FA]\d+\b", "\n".join(l for l in arg_txt.splitlines() if l not in tl)))):
        if eid in qc_bad:
            gaps.append(("amber", f"argument.md cites {eid}, whose quote the quote check marks {qc_bad[eid]}."))

    # ---- render
    def esc(s):
        return html.escape(s or "")
    gap_html = "".join(f'<li class="{l}">{esc(t)}</li>' for l, t in sorted(gaps, key=lambda g: g[0] != "red")) or '<li class="ok">No gaps found by the checks that could run.</li>'
    ref_html = "".join(f"<tr><td>{esc(s)}</td><td>{esc(c[0])}</td><td>{esc(c[1][:110])}</td><td class=\"{'bad' if is_flag(c[2]) else ''}\">{esc(c[2])}</td></tr>" for s, c in ref_rows) or '<tr><td colspan="4">No reference check has run yet.</td></tr>'
    files = []
    for f in sorted(glob.glob(P("*.md")) + glob.glob(P("*.txt"))):
        n = os.path.basename(f)
        if n == "dashboard.html":
            continue
        who = WHO.get(n) or ("script" if n.startswith("refcheck-") else "Critic" if n.startswith("critic-") else "colleague" if n.startswith("checkpoint-") else "Fresh eyes" if n.startswith("fresh-eyes") else "Librarian" if n.startswith("evidence-") else "unknown: not part of the engine's file list")
        tplf = os.path.join(root, "templates", n)
        if os.path.exists(tplf) and rd(f).strip() == rd(tplf).strip():
            when = "template, not written yet"
        else:
            when = mtime(f).astimezone().strftime("%H:%M:%S") + " (last change)"
        files.append(f"<tr><td>{esc(n)}</td><td>{esc(who)}</td><td>{when}</td></tr>")
    readas = read_as_counts(ev)
    brief = esc(rd(P("brief.md")))
    now = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M (your computer's time)")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Session dashboard</title><style>
:root{{--bg:#fbfaf7;--fg:#1d2327;--mute:#5f6b72;--card:#fff;--line:#e3e0d8;--red:#b3261e;--amber:#9a6200;--ok:#2e6b3a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16191b;--fg:#e8e6e1;--mute:#a0a8ad;--card:#1f2326;--line:#33393d;--red:#ff8a80;--amber:#ffcc66;--ok:#8fd19e}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;padding:16px;max-width:1000px;margin:auto}}
h1{{font-size:1.3rem;margin:.2em 0}}h2{{font-size:1rem;margin:0 0 .4em}}section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}}
.strip{{color:var(--mute)}}ul.gaps{{margin:0;padding-left:1.2em}}li.red{{color:var(--red);font-weight:600}}li.amber{{color:var(--amber)}}li.ok{{color:var(--ok)}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}}td.bad{{color:var(--red);font-weight:600}}
pre{{white-space:pre-wrap;font:13px/1.45 ui-monospace,Menlo,monospace;margin:0}}.n{{font-size:1.4rem;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
</style></head><body>
<h1>Research Intelligence Engine · {esc(os.path.basename(sess))}</h1>
<p class="strip">Mode: {esc(MODE_GLOSS.get(status.get('Mode', '?').strip(), status.get('Mode', '?')))} · step: {esc(status.get('Step','?'))} · round: {esc(status.get('Round','?'))} · built from the files by scripts/dashboard.py at {now}</p>
<section><h2>Waiting on you</h2><p>{esc(status.get('Waiting on you','(not recorded in status.md)'))}</p><p class="strip">Next: {esc(status.get('Next',''))}</p></section>
<section><h2>Needs a look</h2><ul class="gaps">{gap_html}</ul></section>
<section><h2>Numbers</h2><div class="grid">
<div><div class="n">{len(ev_ids)}</div>evidence items ({readas['full text']} full text · {readas['abstract only']} abstract only · {readas['no access']} no access)</div>
<div><div class="n">{sum(1 for _, c in ref_rows if is_flag(c[2])) if ref_rows else 'none yet'}</div>{'reference flags (each paper once)' if ref_rows else 'reference check not run yet'}</div>
<div><div class="n">{rounds}</div>Critic rounds ({esc(round_line)})</div>
<div><div class="n">{agree}/{n_same}</div>decisions where you and the colleague agreed (its view shown after yours)</div>
<div><div class="n">{f"{counts['VERIFIED']}/{counts['UNVERIFIED']}/{counts['CONTRADICTED']}" if fe_path else 'not run yet'}</div>Fresh eyes: verified / unverified / contradicted{' (' + esc(os.path.basename(fe_path)) + ')' if fe_path else ''}</div>
<div><div class="n">{f"{n_open}/{len(th)}" if th else 'none yet'}</div>open threads without a recorded answer (open-threads.md)</div></div></section>
<section><h2>Your brief{' · sealed ' + local(bseal) if bseal else ' · not sealed'}</h2><pre>{brief}</pre></section>
<section><h2>Reference checks</h2><table><tr><th>File</th><th>Identifier</th><th>Resolves to</th><th>Flags</th></tr>{ref_html}</table></section>
<section><h2>Files and who wrote them</h2><table><tr><th>File</th><th>Written by</th><th>Time (your computer's)</th></tr>{''.join(files)}</table></section>
</body></html>"""
    write(P("dashboard.html"), page)
    reds = sum(1 for l, _ in gaps if l == "red")
    print(f"DASHBOARD {os.path.abspath(P('dashboard.html'))} · {reds} red gap(s), {len(gaps) - reds} amber (open it in a browser; reload after each step)")
    for l, t in gaps:
        print(f"  [{l}] {t}")


if __name__ == "__main__":
    main()
