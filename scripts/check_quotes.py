#!/usr/bin/env python3
"""Check that the quotes in the evidence files are really in the saved full texts.

Usage: python3 scripts/check_quotes.py sessions/<slug>
Writes sessions/<slug>/quotecheck.md (rerun after every new evidence file; it covers all of them).

What it does (plain language): for every evidence entry with a quote, it finds the
paper's saved full text in papers/ (by DOI or PMCID, from the header fulltext.py
writes) and looks for the quote there, ignoring case, punctuation and spacing.
A quote with an ellipsis (… or ...) is split into parts; each part must be found,
in order. It reports:
  FOUND                      every part is in the text, in order
  ELLIPSIS SPANS N WORDS     the parts are there, but the "…" skips N words and at
                             least one sentence end: read the skipped text, since a
                             qualifier ("For X regions,") may have been cut
  JOINED WITHOUT ELLIPSIS    the quote's sentences are in the text, but not next to
                             each other, and no "…" marks the gap
  NOT FOUND                  a part is not in the saved text (how many words matched)
  NOT CHECKABLE              no saved full text for this entry (abstract only, PDF,
                             or no access); the script cannot say anything about it
Short quoted names (fewer than 4 words) are skipped. A found quote can still be
used out of context; this check only shows that the words and their order are real.
"""
import bisect
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _md import col, ids_in, rd, tables, utf8_console, write  # noqa: E402

QUOTE_RE = re.compile(r"[\"“”„«»]([^\"“”„«»]{12,}?)[\"“”«»]")
ELLIPSIS_RE = re.compile(r"\s*(?:\[\s*(?:\.\s*){3}\]|\[\s*…\s*\]|…|\.\s?\.\s?\.)\s*")
SPAN_LIMIT = 25  # words an ellipsis may skip inside one sentence without comment


def tokens_with_ends(text):
    """Lower-case word tokens; for each, whether a sentence ends right after it."""
    toks, ends, starts = [], [], []
    for m in re.finditer(r"[A-Za-z0-9]+", text):
        toks.append(m.group().lower())
        starts.append(m.start())
        ends.append(bool(re.match(r"[.!?][\"”')\]]*\s+[\"“(\[]?[A-Z0-9]", text[m.end():m.end() + 6])) or text[m.end():m.end() + 2].startswith("\n"))
    return toks, ends


def words(s):
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", s)]


def unfuse(text):
    """Older saved texts glue reference numbers to words ("diverged17"); split them off."""
    return re.sub(r"\b([A-Za-z]{3,})(\d{1,3})\b", r"\1 \2", text)


class Text:
    def __init__(self, raw):
        self.toks, self.ends = tokens_with_ends(raw)
        self.joined = " " + " ".join(self.toks) + " "
        self.offsets, pos = [], 1
        for t in self.toks:
            self.offsets.append(pos)
            pos += len(t) + 1

    def find(self, frag, start_tok=0):
        """Token index of frag (a word list) at or after start_tok, or -1."""
        if not frag:
            return -1
        start_char = self.offsets[start_tok] - 1 if start_tok < len(self.offsets) else len(self.joined)
        i = self.joined.find(" " + " ".join(frag) + " ", start_char)
        return -1 if i < 0 else bisect.bisect_left(self.offsets, i + 1)

    def longest_prefix(self, frag):
        n = 0
        for k in range(len(frag), 0, -1):
            if self.find(frag[:k]) >= 0:
                n = k
                break
        return n


def check_quote(q, text):
    parts = [p for p in ELLIPSIS_RE.split(q) if words(p)]
    if not parts:
        return None
    pos, notes, spans = 0, [], []
    prev_end = None
    for k, p in enumerate(parts):
        w = words(p)
        i = text.find(w, pos)
        if i < 0 and "[" in p:  # "[d]", "[sic]": the quoter's insertions, not the source's words (citations like [14] are tried first)
            w = words(re.sub(r"\[[^\]]*\]", " ", p))
            i = text.find(w, pos)
        if i < 0:
            # maybe two sentences joined with no ellipsis
            sents = [words(s) for s in re.split(r"(?<=[.!?])\s+", p) if words(s)]
            if len(sents) > 1:
                idx = [text.find(s) for s in sents]
                if all(x >= 0 for x in idx):
                    gaps = [idx[j + 1] - (idx[j] + len(sents[j])) for j in range(len(sents) - 1)]
                    return "JOINED WITHOUT ELLIPSIS", f"its sentences are in the text but apart (gaps of {', '.join(map(str, gaps))} words) and no … marks it"
            return "NOT FOUND", f"part {k + 1} of {len(parts)}: only its first {text.longest_prefix(w)} of {len(w)} words match the saved text"
        if prev_end is not None:
            gap = i - prev_end
            crosses = any(text.ends[prev_end - 1:i])
            if gap < 0:
                return "NOT FOUND", f"part {k + 1} is in the text, but before part {k}"
            if crosses and gap >= 4:  # a figure label or a reference number skipped across ")." is not worth a flag
                spans.append(gap)
            elif gap > SPAN_LIMIT:
                spans.append(gap)
        prev_end = i + len(w)
        pos = prev_end
    if spans:
        return f"ELLIPSIS SPANS {max(spans)} WORDS", "the … skips text that includes a sentence end; read what was left out"
    return "FOUND", ""


def saved_texts(session):
    idx = {}
    for p in glob.glob(os.path.join(session, "papers", "**", "*.txt"), recursive=True):
        head = rd(p)[:2000]
        for key in re.findall(r"^(?:PMCID|DOI):\s*(\S+)", head, re.M):
            idx.setdefault(key.lower(), p)
    return idx


def main():
    utf8_console()
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
            print(f"NO SUCH SESSION FOLDER: {sys.argv[1]}")
        sys.exit(2)
    s = sys.argv[1].rstrip("/")
    idx = saved_texts(s)
    cache, rows = {}, []
    for ef in sorted(glob.glob(os.path.join(s, "evidence-*.md"))):
        for header, body in tables(rd(ef)):
            ci_q = col(header, "quote")
            if ci_q is None or col(header, "read as") is None:
                continue  # evidence tables only (not drift checks or query logs)
            for cells in body:
                m = re.search(r"\bE-[FA]\d+\b", cells[0] if cells else "")
                if not m or ci_q >= len(cells):
                    continue
                quotes = [q for q in QUOTE_RE.findall(cells[ci_q]) if len(words(q)) >= 4]
                if not quotes:
                    continue
                row_text = " ".join(cells)
                dois, _ = ids_in(row_text)
                keys = list(dois) + ["pmc" + x for x in re.findall(r"\bPMC(\d+)", row_text, re.I)]
                path = next((idx[k] for k in keys if k in idx), "")
                for q in quotes:
                    if not path:
                        rows.append((m.group(0), os.path.basename(ef), "-", q, "NOT CHECKABLE", "no saved full text for this entry"))
                        continue
                    if path not in cache:
                        cache[path] = (Text(rd(path)), Text(unfuse(rd(path))))
                    res = check_quote(q, cache[path][0])
                    if res and res[0] != "FOUND":
                        res2 = check_quote(unfuse(q), cache[path][1])
                        res = res2 if res2 and res2[0] == "FOUND" else res
                    if res:
                        rows.append((m.group(0), os.path.basename(ef), os.path.relpath(path, s), q, res[0], res[1]))
    count = lambda pred: sum(1 for r in rows if pred(r[4]))
    found = count(lambda x: x == "FOUND")
    look = count(lambda x: x.startswith(("ELLIPSIS", "JOINED")))
    missing = count(lambda x: x == "NOT FOUND")
    unc = count(lambda x: x == "NOT CHECKABLE")
    cellsafe = lambda t: re.sub(r"\s+", " ", t).replace("|", "/")
    out = ["# Quote check", "",
           f"Checked {len(rows)} quotes from the evidence files: {found} found as quoted, {look} need a look (ellipsis or join), "
           f"{missing} not found in the saved text, {unc} not checkable (no saved full text). Made by `scripts/check_quotes.py`; do not edit by hand.", "",
           "| Evidence | From | Saved text | Quote (start) | Result | Detail |", "|---|---|---|---|---|---|"]
    for eid, ef, path, q, res, det in rows:
        out.append(f"| {eid} | {ef} | {path} | {cellsafe(q[:90])}{'…' if len(q) > 90 else ''} | {res} | {cellsafe(det)} |")
    if not rows:
        out.append("| (no quotes found in the evidence tables) | | | | NOTHING CHECKED | |")
    write(os.path.join(s, "quotecheck.md"), "\n".join(out) + "\n")
    print(out[2])
    for r in rows:
        if r[4] not in ("FOUND", "NOT CHECKABLE"):
            print(f"  {r[0]} ({r[1]}): {r[4]}: {r[5]}")
    print(f"WROTE {os.path.join(s, 'quotecheck.md')}")


if __name__ == "__main__":
    main()
