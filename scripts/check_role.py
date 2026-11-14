#!/usr/bin/env python3
"""Check that a role's output file is complete.

Usage: python3 scripts/check_role.py <role> sessions/<slug>/<output file>
Roles: deep-analyst · librarian · critic · fresh-eyes · synthesis

What it does: looks for the headings each role must write. A role can be cut
off mid-way (a provider's safety filter or a length limit stopped one in the
first test), and a half-finished file looks finished unless something checks.
Exit code 0 = complete; 1 = sections missing (listed), so the colleague can
rerun only the missing part or tell the researcher exactly what is absent.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import rd, utf8_console  # noqa: E402

REQUIRED = {
    "deep-analyst": ["## 1 ·", "## 2 ·", "## 3 ·", "## 4 ·", "## 5 ·", "## 6 ·"],
    "librarian": ["## Query log", "## Evidence", "## Drift check", "## One passage for you", "## What I did not search"],
    "critic": ["## 1 ·", "## 2 ·", "## 3 ·", "## 4 ·", "## 5 ·", "## 6 ·", "## 7 ·"],
    "fresh-eyes": ["## Verdicts", "## Summary"],
    "synthesis": ["## Answer", "## Main caveat", "## What would settle it"],
}


def main():
    utf8_console()
    if len(sys.argv) != 3 or sys.argv[1] not in REQUIRED:
        print(__doc__)
        sys.exit(2)
    role, path = sys.argv[1], sys.argv[2]
    if not rd(path).strip():
        print(f"INCOMPLETE {path}: file missing or empty")
        sys.exit(1)
    text = rd(path)
    missing = [h for h in REQUIRED[role] if h not in text]
    tail = text.rstrip()[-1:]
    if missing:
        print(f"INCOMPLETE {path}: missing {', '.join(missing)}")
        sys.exit(1)
    if tail not in ".|)]*\"'`»”?!" and not tail.isalnum():
        print(f"CHECK {path}: all sections present, but the file ends oddly; look at its last lines")
    print(f"COMPLETE {path}: all {len(REQUIRED[role])} required sections present")


if __name__ == "__main__":
    main()
