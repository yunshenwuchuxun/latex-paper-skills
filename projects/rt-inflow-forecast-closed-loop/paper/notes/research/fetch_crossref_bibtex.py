#!/usr/bin/env python
"""Fetch BibTeX entries from Crossref for a DOI list and write ref.bib.

Dependency-free (stdlib only). Uses Crossref's transform endpoint as the online
verification source.

Usage:
  python fetch_crossref_bibtex.py --doi-file seed_dois.txt --out-bib ..\\..\\ref.bib
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path


UA = "latex-arxiv-skill/0.1 (mailto:noreply@example.com)"
STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "into",
    "on",
    "for",
    "with",
    "via",
    "using",
    "by",
    "from",
    "towards",
    "toward",
}


def read_dois(path: Path) -> list[str]:
    raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    cleaned: list[str] = []
    for raw in raw_lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cleaned.append(line)

    # Stable order + dedupe
    seen: set[str] = set()
    out: list[str] = []
    for doi in cleaned:
        key = doi.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(doi)
    return out


def ascii_sanitize(text: str) -> str:
    # Prefer ASCII for pdflatex portability.
    replacements = {
        "\u00a0": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "--",
        "\u2014": "---",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": "\"",
        "\u201d": "\"",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    if all(ord(ch) < 128 for ch in text):
        return text
    # Last resort: drop diacritics (rare in our seed list).
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def latex_sanitize(text: str) -> str:
    # Crossref occasionally returns HTML entities in venue names.
    text = text.replace("&amp;", r"\&")
    # Escape bare '&' for LaTeX table safety.
    text = re.sub(r"(?<!\\)&", r"\&", text)
    return text


def fetch_bibtex(doi: str, *, timeout_s: int) -> str:
    quoted = urllib.parse.quote(doi)
    url = f"https://api.crossref.org/works/{quoted}/transform/application/x-bibtex"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8", errors="replace").strip()


def extract_field(bibtex: str, field: str) -> str:
    # Crossref BibTeX is usually one line; allow newlines.
    pattern = r"(?i)\b" + re.escape(field) + r"\s*=\s*\{(.*?)\}"
    m = re.search(pattern, bibtex, flags=re.DOTALL)
    return (m.group(1) if m else "").strip()


def first_author_family(author_field: str) -> str:
    if not author_field:
        return "unknown"
    first = author_field.split(" and ", 1)[0].strip()
    if "," in first:
        family = first.split(",", 1)[0].strip()
    else:
        family = first.split()[-1].strip()
    family = re.sub(r"[^A-Za-z0-9]+", "", family).lower()
    return family or "unknown"


def extract_year(year_field: str) -> str:
    m = re.search(r"\b(19|20)\d{2}\b", year_field or "")
    return m.group(0) if m else "0000"


def title_first_word(title: str) -> str:
    cleaned = re.sub(r"[{}]", "", title)
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", " ", cleaned)
    cleaned = cleaned.replace("-", " ")
    words = [w for w in cleaned.split() if w]
    for word in words:
        lower = word.lower()
        if lower in STOPWORDS:
            continue
        token = re.sub(r"[^a-z0-9]+", "", lower)
        if token:
            return token
    return "paper"


def make_key(bibtex: str) -> str:
    author = extract_field(bibtex, "author")
    year = extract_field(bibtex, "year")
    title = extract_field(bibtex, "title")
    return f"{first_author_family(author)}{extract_year(year)}{title_first_word(title)}"


def rewrite_key(bibtex: str, new_key: str) -> str:
    m = re.search(r"@(?P<typ>\w+)\s*\{\s*(?P<key>[^,]+)\s*,", bibtex)
    if not m:
        return bibtex
    start, end = m.span("key")
    return bibtex[:start] + new_key + bibtex[end:]


def normalize_fields(bibtex: str) -> str:
    # Keep field names lowercase for consistency; preserve values.
    bibtex = re.sub(r"\bDOI\s*=", "doi =", bibtex)
    bibtex = re.sub(r"\bURL\s*=", "url =", bibtex)
    bibtex = re.sub(r"\bISSN\s*=", "issn =", bibtex)
    bibtex = re.sub(r"\bISBN\s*=", "isbn =", bibtex)

    doi = extract_field(bibtex, "doi")
    if doi:
        bibtex = re.sub(
            r"(?i)\burl\s*=\s*\{[^}]*\}",
            f"url = {{https://doi.org/{doi}}}",
            bibtex,
        )
    return bibtex


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi-file", type=Path, required=True)
    ap.add_argument("--out-bib", type=Path, required=True)
    ap.add_argument("--timeout-s", type=int, default=20)
    ap.add_argument("--sleep-s", type=float, default=0.2)
    args = ap.parse_args()

    dois = read_dois(args.doi_file)
    if not dois:
        print("error: no DOIs found", file=sys.stderr)
        return 1

    entries: list[str] = []
    failures: list[str] = []
    seen_keys: set[str] = set()

    for doi in dois:
        try:
            raw = fetch_bibtex(doi, timeout_s=args.timeout_s)
        except Exception as exc:
            failures.append(f"{doi}\t{type(exc).__name__}: {exc}")
            continue

        bib = ascii_sanitize(raw)
        bib = latex_sanitize(bib)
        key = make_key(bib)
        base = key
        suffix_ord = ord("a")
        while key in seen_keys:
            key = base + chr(suffix_ord)
            suffix_ord += 1
        seen_keys.add(key)

        bib = rewrite_key(bib, key)
        bib = normalize_fields(bib).rstrip() + "\n"
        entries.append(bib)

        time.sleep(max(0.0, float(args.sleep_s)))

    header = "\n".join(
        [
            "% Verified BibTeX entries (Crossref).",
            "% Generated by notes/research/fetch_crossref_bibtex.py",
            "",
        ]
    )
    out_text = header + "\n".join(e.strip() + "\n" for e in entries) + "\n"
    args.out_bib.parent.mkdir(parents=True, exist_ok=True)
    args.out_bib.write_text(out_text, encoding="utf-8")

    print(f"Wrote {len(entries)} BibTeX entries to: {args.out_bib}")
    if failures:
        print(f"Failures: {len(failures)}", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
