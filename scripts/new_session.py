#!/usr/bin/env python3
"""Create a new session folder from the templates, or resume an existing one.

Usage:
  python3 scripts/new_session.py "<short slug>"         create sessions/<YYYY-MM-DD>-<slug>/
  python3 scripts/new_session.py --resume <folder name>  make an existing session the active one again
  python3 scripts/new_session.py --list                  list sessions, newest first, with their step

Creates brief.md, decisions.md, argument.md, status.md, colleague-views.md, an
empty my-papers.txt and the folders papers/for, papers/against and papers/mine
(papers/mine is for PDFs you add yourself, e.g. through your library's access).
Records the session as the active one (sessions/ACTIVE); resuming rewrites it.
"""
import datetime as dt
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import rd, utf8_console, write  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS = os.path.join(ROOT, "sessions")


def main():
    utf8_console()
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--list":
        names = sorted((n for n in os.listdir(SESSIONS) if os.path.isdir(os.path.join(SESSIONS, n))), reverse=True) if os.path.isdir(SESSIONS) else []
        for n in names:
            st = dict(re.findall(r"^- \*\*(.+?):\*\*\s*(.*)$", rd(os.path.join(SESSIONS, n, "status.md")), re.M))
            print(f"{n} · step: {st.get('Step', '?')} · stop: {st.get('Stop reason', '?')}")
        print(f"{len(names)} session(s)")
        return
    if sys.argv[1] == "--resume":
        name = os.path.basename((sys.argv[2] if len(sys.argv) > 2 else "").rstrip("/"))
        path = os.path.join(SESSIONS, name)
        if not name or not os.path.isdir(path):
            print(f"NO SUCH SESSION {path}; see: python3 scripts/new_session.py --list")
            sys.exit(2)
        os.makedirs(os.path.join(path, "papers", "mine"), exist_ok=True)
        write(os.path.join(SESSIONS, "ACTIVE"), name + "\n")
        print(f"RESUMED sessions/{name} (now the active session)\nFOLDER {path}")
        return
    slug = re.sub(r"[^a-z0-9]+", "-", sys.argv[1].lower()).strip("-")[:40] or "session"
    name = f"{dt.date.today().isoformat()}-{slug}"
    path = os.path.join(SESSIONS, name)
    if os.path.exists(path):
        print(f"EXISTS {path} (resume it with --resume {name}, or choose another slug)")
        sys.exit(2)
    for sub in ("for", "against", "mine"):
        os.makedirs(os.path.join(path, "papers", sub))
    for t in ("brief.md", "decisions.md", "argument.md", "status.md", "colleague-views.md"):
        shutil.copy(os.path.join(ROOT, "templates", t), os.path.join(path, t))
    write(os.path.join(path, "my-papers.txt"), "")
    write(os.path.join(SESSIONS, "ACTIVE"), name + "\n")
    print(f"CREATED sessions/{name}\nFOLDER {path}\nDASHBOARD (after the first dashboard.py run) {os.path.join(path, 'dashboard.html')}")


if __name__ == "__main__":
    main()
