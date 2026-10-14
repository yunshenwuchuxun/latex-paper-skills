#!/usr/bin/env python3
"""Generate/refresh notes/literature-notes.md from ref.bib (no web calls).

Design goals:
- Always include at least metadata stubs for each paper (citekey/title/authors/year/links).
- Default to cited-only mode when main.tex exists and contains citations.
- Preserve a manual notes section on regeneration.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from paper_utils import extract_citation_commands, parse_bibtex_entries  # noqa: E402


AUTO_BEGIN = "<!-- AUTO-GENERATED: literature-notes v1 -->"
AUTO_END = "<!-- END AUTO-GENERATED -->"
MANUAL_HEADER = "## Manual Notes"


@dataclass(frozen=True)
class BibMeta:
    key: str
    entry_type: str
    title: str
    authors: str
    year: str
    venue: str
    url: str
    doi: str
    arxiv: str


def _collapse_ws(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _read_braced(text: str, start: int) -> tuple[str, int]:
    depth = 0
    out: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            if depth > 1:
                out.append(ch)
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return "".join(out), i + 1
            out.append(ch)
        else:
            out.append(ch)
        i += 1
    return "".join(out), i


def _read_quoted(text: str, start: int) -> tuple[str, int]:
    out: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == '"' and (i == 0 or text[i - 1] != "\\"):
            return "".join(out), i + 1
        out.append(ch)
        i += 1
    return "".join(out), i


def _extract_field(entry_text: str, field: str) -> str:
    pattern = re.compile(rf"(?im)^\s*{re.escape(field)}\s*=\s*", re.MULTILINE)
    match = pattern.search(entry_text)
    if not match:
        return ""
    i = match.end()
    while i < len(entry_text) and entry_text[i].isspace():
        i += 1
    if i >= len(entry_text):
        return ""
    if entry_text[i] == "{":
        value, _ = _read_braced(entry_text, i)
        return _collapse_ws(value)
    if entry_text[i] == '"':
        value, _ = _read_quoted(entry_text, i + 1)
        return _collapse_ws(value)
    end = i
    while end < len(entry_text) and entry_text[end] not in ",\n\r":
        end += 1
    return _collapse_ws(entry_text[i:end])


def _infer_venue(entry_text: str) -> str:
    for field in ("journal", "booktitle", "publisher", "institution", "howpublished"):
        value = _extract_field(entry_text, field)
        if value:
            return value
    return ""


def _infer_arxiv(entry_text: str) -> str:
    eprint = _extract_field(entry_text, "eprint")
    if eprint and re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", eprint):
        return eprint
    url = _extract_field(entry_text, "url")
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?", url, re.IGNORECASE)
    return match.group(1) if match else ""


def _parse_meta(entry: dict[str, Any]) -> BibMeta:
    text = str(entry.get("text") or "")
    key = str(entry.get("key") or "")
    entry_type = str(entry.get("entry_type") or "")

    return BibMeta(
        key=key,
        entry_type=entry_type,
        title=_extract_field(text, "title"),
        authors=_extract_field(text, "author"),
        year=_extract_field(text, "year"),
        venue=_infer_venue(text),
        url=_extract_field(text, "url"),
        doi=_extract_field(text, "doi"),
        arxiv=_infer_arxiv(text),
    )


def _extract_cited_keys(tex_path: Path) -> set[str]:
    if not tex_path.exists():
        return set()
    content = tex_path.read_text(encoding="utf-8-sig")
    keys: set[str] = set()
    for cmd in extract_citation_commands(content):
        for key in cmd.get("keys") or []:
            if key:
                keys.add(str(key).strip())
    return keys


def _read_manual_notes(existing: str) -> str:
    if not existing:
        return f"{MANUAL_HEADER}\n(Write free-form notes here. This section should be preserved across refreshes.)\n"
    index = existing.find(MANUAL_HEADER)
    if index == -1:
        return f"{MANUAL_HEADER}\n(Write free-form notes here. This section should be preserved across refreshes.)\n"
    return existing[index:].rstrip() + "\n"


def _format_paper_section(meta: BibMeta, cited: bool) -> str:
    title = meta.title or "(title missing in BibTeX)"
    year = meta.year or "????"
    lines: list[str] = [f"### {meta.key} - {title} ({year})"]
    lines.append(f"- Entry type: `{meta.entry_type}`")
    if meta.authors:
        lines.append(f"- Authors: {meta.authors}")
    if meta.venue:
        lines.append(f"- Venue: {meta.venue}")
    if meta.arxiv:
        lines.append(f"- arXiv: {meta.arxiv}")
    if meta.doi:
        lines.append(f"- DOI: {meta.doi}")
    if meta.url:
        lines.append(f"- URL: {meta.url}")
    lines.append(f"- Cited in draft: {'yes' if cited else 'no'}")
    lines.append("- Summary (2-3 sentences): TODO")
    lines.append("- Why it matters to this draft: TODO")
    lines.append("- Closest relation to our claim(s): TODO")
    lines.append("- Evidence used from this paper: TODO")
    lines.append("- Risks / caveats: TODO")
    return "\n".join(lines) + "\n"


def generate_notes(*, bib_path: Path, tex_path: Path, output_path: Path, mode: str) -> None:
    existing = output_path.read_text(encoding="utf-8-sig") if output_path.exists() else ""
    manual = _read_manual_notes(existing)

    bib_content = bib_path.read_text(encoding="utf-8-sig")
    entries = parse_bibtex_entries(bib_content)
    metas = [_parse_meta(entry) for entry in entries if entry.get("key")]

    cited_keys = _extract_cited_keys(tex_path)
    if mode == "cited" and cited_keys:
        metas = [meta for meta in metas if meta.key in cited_keys]

    metas.sort(key=lambda meta: (meta.year or "", meta.key), reverse=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = [
        "# Literature Notes",
        "",
        AUTO_BEGIN,
        f"Generated: {now}",
        f"Source: {bib_path.as_posix()}",
        f"Mode: {mode}",
        AUTO_END,
        "",
        "## Papers (auto)",
        "",
    ]

    body: list[str] = []
    if not metas:
        body.append("- (No matching BibTeX entries found yet.)\n")
    else:
        for meta in metas:
            body.append(_format_paper_section(meta, cited=(meta.key in cited_keys)))
            body.append("")

    output = "\n".join(header) + "\n" + "\n".join(body).rstrip() + "\n\n" + manual
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/refresh literature notes from ref.bib (no web calls).")
    parser.add_argument("--project-dir", default=".", help="Paper/project directory.")
    parser.add_argument("--bib", default="ref.bib", help="BibTeX file (relative to project-dir).")
    parser.add_argument("--tex", default="main.tex", help="LaTeX file for cited-only mode (relative to project-dir).")
    parser.add_argument("--output", default="notes/literature-notes.md", help="Output markdown (relative to project-dir).")
    parser.add_argument("--mode", default="cited", choices=["cited", "all"], help="Include cited-only or all bib entries.")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        print(f"error: project dir not found: {project_dir}", file=sys.stderr)
        return 1

    bib_path = (project_dir / args.bib).resolve()
    tex_path = (project_dir / args.tex).resolve()
    output_path = (project_dir / args.output).resolve()

    if not bib_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    "# Literature Notes",
                    "",
                    AUTO_BEGIN,
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Source: {bib_path.as_posix()}",
                    f"Mode: {args.mode}",
                    "Note: `ref.bib` not found yet.",
                    AUTO_END,
                    "",
                    "## Papers (auto)",
                    "",
                    "- (No BibTeX file yet. Populate `ref.bib` then refresh.)",
                    "",
                    MANUAL_HEADER,
                    "(Write free-form notes here. This section should be preserved across refreshes.)",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return 0

    generate_notes(bib_path=bib_path, tex_path=tex_path, output_path=output_path, mode=str(args.mode))
    print(f"Updated literature notes: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
