#!/usr/bin/env python3
"""Save an open-access full text from Europe PMC as plain text.

Usage: python3 scripts/fulltext.py PMC1234567 --out sessions/<slug>/papers/<for|against>/

What it does: asks Europe PMC for the article's open-access full text (XML),
keeps every paragraph in the body in document order (inside sections or not,
including figure and table captions) with section headings, and writes
papers/<PMCID>.txt with the title and DOI on top. Legal open access only;
nothing behind a paywall. If there is no open full text it says so, and the
Librarian records the paper as "abstract only" or "no access". If the body
holds fewer than about 100 words (some notices and letters), it warns: treat
the paper as read from its abstract only.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _http import FetchError, fetch  # noqa: E402
from _md import utf8_console, write  # noqa: E402

MIN_BODY_WORDS = 100


def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def walk(el, lines):
    """Paragraphs anywhere under el, in order; a <sec> adds its heading first."""
    for child in el:
        tag = child.tag if isinstance(child.tag, str) else ""
        if tag == "sec":
            t = child.find("title")
            if t is not None and text_of(t):
                lines.append("")
                lines.append("## " + text_of(t))
            walk(child, lines)
        elif tag == "p":
            if text_of(child):
                lines.append(text_of(child))
        elif tag in ("title", "label"):
            continue  # a section's title is written above; labels ("Figure 1") come with the caption text
        else:
            walk(child, lines)


def main():
    utf8_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("pmcid")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pmcid = a.pmcid.upper() if a.pmcid.upper().startswith("PMC") else "PMC" + a.pmcid
    try:
        xml = fetch(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML", timeout=60)
    except FetchError as e:
        why = ("Europe PMC had a server problem or could not be reached, so try once more later"
               if "404" not in str(e) else "It may be embargoed or outside the open-access subset")
        print(f"NO OPEN FULL TEXT: {pmcid} ({e}). {why}; until a full text is saved, record the paper as abstract only, and do not tell the researcher that reading it would settle anything.")
        sys.exit(3)
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        print(f"FULL TEXT UNREADABLE: {pmcid} ({e})")
        sys.exit(3)
    for parent in root.iter():  # "diverged<sup><xref>17</xref></sup>" -> "diverged 17": keep words and reference numbers apart
        for i, child in enumerate(list(parent)):
            cite = (child.tag == "xref" and child.get("ref-type") == "bibr") or (child.tag == "sup" and child.find(".//xref") is not None)
            before = (parent[i - 1].tail if i else parent.text) or ""
            if cite and before[-1:].isalnum():
                child.text = " " + (child.text or "")
    title = text_of(root.find(".//article-title")) if root.find(".//article-title") is not None else ""
    doi = next((text_of(x) for x in root.iter("article-id") if x.get("pub-id-type") == "doi"), "")
    lines = [f"TITLE: {title}", f"PMCID: {pmcid}", f"DOI: {doi}", "SOURCE: Europe PMC open-access full text", ""]
    abstract = root.find(".//abstract")
    if abstract is not None:
        abs_lines = []
        walk(abstract, abs_lines)  # paragraphs only, so the heading "Abstract" is not glued to the first word
        lines += ["## Abstract"] + ([l for l in abs_lines if l] or [text_of(abstract)]) + [""]
    body = root.find(".//body")
    body_lines = []
    if body is not None:
        walk(body, body_lines)
    lines += body_lines
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, pmcid + ".txt")
    write(path, "\n".join(lines) + "\n")
    words = sum(len(x.split()) for x in lines)
    body_words = sum(len(x.split()) for x in body_lines if not x.startswith("## "))
    print(f"SAVED {path} ({words} words; body {body_words} words)")
    if body_words < MIN_BODY_WORDS:
        print(f"WARNING: only {body_words} words of body text came back"
              f"{' (no body in the open XML)' if body is None else ''}; treat this paper as read from its abstract only "
              "(\"abstract only\" in the Read as column), unless it is a short notice whose full text this is.")


if __name__ == "__main__":
    main()
