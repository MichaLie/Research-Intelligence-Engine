#!/usr/bin/env python3
"""Seal a file the researcher wrote: record its fingerprint and the time.

Usage:
  python3 scripts/seal.py sessions/<slug> brief.md      seal (or re-seal after a revision)
  python3 scripts/seal.py sessions/<slug> --verify      show every seal and whether the file changed since
  python3 scripts/seal.py sessions/<slug> brief.md --question-only
        agents-first mode: seal a brief that so far holds only the question (5+ words);
        the rest of the brief is written later and sealed again

What it does: computes the file's SHA-256 fingerprint and writes it, with the
UTC time, to seals.json in the session folder. Re-sealing adds a new entry and
keeps the old ones, so revisions stay visible. The dashboard uses the seal
times to show whether any agent output appeared before the researcher's own
thinking was written down.
"""
import datetime as dt
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import rd, utf8_console, write  # noqa: E402


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    utf8_console()
    question_only = "--question-only" in sys.argv
    sys.argv = [x for x in sys.argv if x != "--question-only"]
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sess, target = sys.argv[1], sys.argv[2]
    sp = os.path.join(sess, "seals.json")
    seals = json.loads(rd(sp)) if os.path.exists(sp) else {}
    if target == "--verify":
        for name, entries in seals.items():
            p = os.path.join(sess, name)
            last = entries[-1]
            state = "missing" if not os.path.exists(p) else ("unchanged since seal" if sha(p) == last["sha256"] else "CHANGED AFTER SEAL")
            print(f"{name}: sealed {len(entries)}x, last {last['sealed_at']} -> {state}")
        return
    p = os.path.join(sess, target)
    if not os.path.exists(p):
        print(f"SEAL FAILED: {p} does not exist")
        sys.exit(2)
    body = rd(p)
    tpl = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", target)
    tlines = set(rd(tpl).splitlines())
    own = sum(len(line.split()) for line in body.splitlines() if line.strip() and line not in tlines)
    need = 5 if question_only else 15
    if own < need:
        print(f"SEAL REFUSED: {target} has only {own} words beyond the template (needs {need}); is it filled in?")
        sys.exit(2)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    seals.setdefault(target, []).append({"sha256": sha(p), "sealed_at": now, "words": len(body.split())})
    vdir = os.path.join(sess, "versions")
    os.makedirs(vdir, exist_ok=True)
    stem, ext = os.path.splitext(target)
    write(os.path.join(vdir, f"{stem}-v{len(seals[target])}{ext}"), body)  # every sealed version is kept, so revisions stay readable, not just their hash
    write(sp, json.dumps(seals, indent=1))
    print(f"SEALED {target} at {now} (seal #{len(seals[target])}, {len(body.split())} words)")


if __name__ == "__main__":
    main()
