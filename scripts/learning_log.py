#!/usr/bin/env python3
"""Append this session to your own learning log (stays on this machine).

Usage: python3 scripts/learning_log.py sessions/<slug>

What it records in learning/LOG.md: date, question, the expectation and
confidence written in the brief (verbatim, so you can compare your confidence
with the outcome over sessions), mode, rounds, how often you and the
colleague agreed (the colleague's view was shown after you chose),
reference flags in your own list vs in the evidence (each paper once;
"not checked" if no check ran), Fresh-eyes counts, open threads left, and your
own answers to "which expectations held?" and "what would you do
differently?" (from reflection.md, verbatim).
Over several sessions this shows trends: does agreement drift towards 100%?
Do Fresh-eyes contradictions fall? Nothing is sent anywhere.
"""
import datetime as dt
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import agreement, is_flag, latest_fresh_eyes, rd, refcheck_rows, utf8_console, verdict_counts, write  # noqa: E402
from open_threads import answers, threads  # noqa: E402


def main():
    utf8_console()
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        sys.exit(2)
    s = sys.argv[1].rstrip("/")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = lambda n: os.path.join(s, n)
    brief = rd(P("brief.md"))
    sec = lambda n: re.search(rf"^## {n} ·.*?\n(.*?)(?=^## |\Z)", brief, re.S | re.M)
    q, e = sec(1), sec(2)
    question = re.sub(r"\s+", " ", q.group(1)).strip()[:200] if q else "(no question)"
    expected = re.sub(r"\s+", " ", e.group(1)).strip()[:300] if e and e.group(1).strip() else "(not written)"
    status = dict(re.findall(r"^- \*\*(.+?):\*\*\s*(.*)$", rd(P("status.md")), re.M))
    c = verdict_counts(rd(latest_fresh_eyes(s)))

    def flags(pred, files):
        if not files:
            return "not checked"
        return str(sum(1 for _, _, _, fl, _ in refcheck_rows(s, pred) if is_flag(fl)))
    mine = flags(lambda f: "mine" in f, glob.glob(P("refcheck-mine*.md")))
    evid = flags(lambda f: "mine" not in f, glob.glob(P("refcheck-evidence*.md")))
    th, ans = threads(s), answers(s)
    agreed, counted = agreement(rd(P("decisions.md")))
    refl = re.sub(r"^#.*\n", "", rd(P("reflection.md")), count=1).strip() or "(no reflection recorded)"
    entry = f"""
## {dt.date.today().isoformat()} · {os.path.basename(s)}
- Question: {question}
- Expected at the start (brief, question 2): {expected}
- Mode: {status.get('Mode', '?')} · rounds: {len(glob.glob(P('critic-round-*.md')))} · stop: {status.get('Stop reason', '?')}
- Agreement with the colleague (its view shown after yours): {agreed}/{counted}
- Reference flags: {mine} in your own list · {evid} in the evidence found
- Fresh eyes: {c['VERIFIED']} verified · {c['UNVERIFIED']} unverified · {c['CONTRADICTED']} contradicted
- Open threads: {len(th) - sum(1 for t in th if t[0] not in ans)} answered, {sum(1 for t in th if t[0] not in ans)} left open
- In your words:
{refl}
"""
    os.makedirs(os.path.join(root, "learning"), exist_ok=True)
    lp = os.path.join(root, "learning", "LOG.md")
    if not os.path.exists(lp):
        write(lp, "# Your learning log\n\nOne entry per session: what you expected, what the checks found, how often you and the colleague agreed, and your own reflection. Stays on this machine.\n")
    write(lp, entry, mode="a")
    print(f"APPENDED to {lp}")


if __name__ == "__main__":
    main()
