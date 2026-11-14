#!/usr/bin/env python3
"""Rewrite the session's status.md in one go, so no field is left stale.

Usage:
  python3 scripts/status.py sessions/<slug> --step "4 · find" --round 1 \
      --last "Both Librarians finished; references checked" \
      --next "You read the passage they chose" --waiting "Two or three sentences in reading-notes.md" \
      [--mode you-first|agents-first] [--stop "..."]

What it does: every field must be given each time (mode and stop reason are
kept from the previous status if not given). The first test showed a status
file saying "closed" while still listing the next step of an earlier stage.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import rd, utf8_console, write  # noqa: E402

MODES = ("you-first", "agents-first")  # the exact words the dashboard reads


def main():
    utf8_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    for f in ("step", "round", "last", "next", "waiting"):
        ap.add_argument("--" + f, required=True)
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--stop")
    a = ap.parse_args()
    if not os.path.isdir(a.session):
        print(f"NO SUCH SESSION FOLDER: {a.session}")
        sys.exit(2)
    p = os.path.join(a.session, "status.md")
    old = dict(re.findall(r"^- \*\*(.+?):\*\*\s*(.*)$", rd(p), re.M))
    fields = [("Mode", a.mode or old.get("Mode", "you-first")), ("Step", a.step), ("Round", a.round),
              ("Last thing that happened", a.last), ("Next", a.next), ("Waiting on you", a.waiting),
              ("Stop reason", a.stop or old.get("Stop reason", "(filled at the end)"))]
    write(p, "# Status\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in fields) + "\n")
    print(f"STATUS {p}: step {a.step}, round {a.round}")


if __name__ == "__main__":
    main()
