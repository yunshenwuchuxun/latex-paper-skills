#!/usr/bin/env python3
"""Recommend and audit citations using venue and source-quality policy."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from arxiv_registry import connect, ensure_initialized, init_schema
from paper_utils import (
    count_citations,
    extract_citation_commands,
    extract_section_events,
    find_section_path_for_position,
    load_paper_config,
    normalize_text,
    normalize_text_tokens,
    parse_bibtex_entries,
)
from source_policy_utils import assess_work, ensure_policy_schema, load_external_metadata, resolve_work_ids, venue_matches


def read_issue_rows(path: Path) -> list[dict[str, str]]:
    """Read issues CSV rows."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_document_tokens(issue_row: dict[str, str]) -> set[str]:
    """Build normalized keyword tokens from an issue row."""
    fields = [
        issue_row.get("Title", ""),
        issue_row.get("Section_Path", ""),
        issue_row.get("Description", ""),
        issue_row.get("Visualization", ""),
        issue_row.get("Acceptance", ""),
    ]
    tokens: set[str] = set()
    for field in fields:
        for token in normalize_text_tokens(field):
            if len(token) >= 3:
                tokens.add(token)
    return tokens


def work_candidate_rows(conn: sqlite3.Connection, work_ids: list[int]) -> list[sqlite3.Row]:
    """Load candidate rows with assessment metadata."""
    rows: list[sqlite3.Row] = []
    for work_id in work_ids:
        row = conn.execute(
            """
            SELECT w.work_id, w.arxiv_id, w.title, w.summary, w.published, w.journal_ref, w.doi,
                   sa.source_tier, sa.quality_score, sa.assessment_reason,
                   sa.canonical_venue, sa.preferred_citation_url, sa.has_formal_version
            FROM works w
            LEFT JOIN source_assessments sa ON sa.work_id = w.work_id
            WHERE w.work_id = ?;
            """,
            (work_id,),
        ).fetchone()
        if row is not None:
            rows.append(row)
    return rows


def recommendation_score(row: sqlite3.Row, issue_tokens: set[str], preferred_venues: list[str]) -> float:
    """Score a candidate source for an issue."""
    haystack = " ".join(
        [
            str(row["title"] or ""),
            str(row["summary"] or ""),
            str(row["canonical_venue"] or row["journal_ref"] or ""),
        ]
    )
    haystack_tokens = set(token for token in normalize_text_tokens(haystack) if len(token) >= 3)
    overlap = len(issue_tokens & haystack_tokens)
    score = overlap * 8.0
    quality_score = int(row["quality_score"] or 0)
    score += quality_score
    if venue_matches(str(row["canonical_venue"] or row["journal_ref"] or ""), preferred_venues):
        score += 10.0
    if row["source_tier"] == "A":
        score += 5.0
    elif row["source_tier"] == "B":
        score += 2.0
    return score


def cmd_recommend(args: argparse.Namespace) -> int:
    issues = read_issue_rows(args.issues)
    issue_row = next((row for row in issues if row.get("ID") == args.issue_id), None)
    if issue_row is None:
        print(f"error: issue not found: {args.issue_id}", file=sys.stderr)
        return 1

    config = load_paper_config(args.project_dir)
    preferred_venues = [str(item) for item in (config.get("preferred_venues") or [])]
    target_venue = str(config.get("target_venue") or "")
    if target_venue and target_venue not in preferred_venues:
        preferred_venues.insert(0, target_venue)

    with connect(args.db) as conn:
        init_schema(conn)
        ensure_initialized(conn)
        ensure_policy_schema(conn)
        work_ids = resolve_work_ids(conn, search_id=args.search_id, arxiv_ids=args.arxiv_id)
        issue_tokens = build_document_tokens(issue_row)

        ranked: list[tuple[float, sqlite3.Row]] = []
        for row in work_candidate_rows(conn, work_ids):
            if row["quality_score"] is None:
                assessment = assess_work(
                    conn,
                    work_id=int(row["work_id"]),
                    config=config,
                    timeout_s=args.timeout_s,
                    refresh=args.refresh,
                )
                row = conn.execute(
                    """
                    SELECT w.work_id, w.arxiv_id, w.title, w.summary, w.published, w.journal_ref, w.doi,
                           sa.source_tier, sa.quality_score, sa.assessment_reason,
                           sa.canonical_venue, sa.preferred_citation_url, sa.has_formal_version
                    FROM works w
                    LEFT JOIN source_assessments sa ON sa.work_id = w.work_id
                    WHERE w.work_id = ?;
                    """,
                    (assessment["work_id"],),
                ).fetchone()
            if row is None:
                continue
            score = recommendation_score(row, issue_tokens, preferred_venues)
            ranked.append((score, row))

        ranked.sort(key=lambda item: item[0], reverse=True)
        print(
            f"Recommendations for {args.issue_id} ({issue_row.get('Section_Path') or 'N/A'}) | "
            f"source_policy={issue_row.get('Source_Policy') or 'N/A'}"
        )
        for score, row in ranked[: args.limit]:
            print(
                f"- score={score:.1f} tier={row['source_tier'] or 'N/A'} venue={row['canonical_venue'] or row['journal_ref'] or 'N/A'} "
                f"title={row['title']} url={row['preferred_citation_url'] or 'N/A'}"
            )
    return 0


def cmd_audit_bib(args: argparse.Namespace) -> int:
    bib_path = args.project_dir / "ref.bib"
    if not bib_path.exists():
        print(f"error: ref.bib not found in {args.project_dir}", file=sys.stderr)
        return 1

    content = bib_path.read_text(encoding="utf-8")
    entries = parse_bibtex_entries(content)
    if not entries:
        print("No BibTeX entries found.")
        return 0

    flagged = 0
    with connect(args.db) as conn:
        init_schema(conn)
        ensure_initialized(conn)
        ensure_policy_schema(conn)
        for entry in entries:
            key_row = conn.execute(
                "SELECT work_id FROM citation_keys WHERE key = ?;",
                (entry["key"],),
            ).fetchone()
            if key_row is None:
                continue
            work_id = int(key_row["work_id"])
            assessment = conn.execute(
                "SELECT * FROM source_assessments WHERE work_id = ?;",
                (work_id,),
            ).fetchone()
            metadata = load_external_metadata(conn, work_id)
            if assessment is None or metadata is None:
                continue
            uses_arxiv_bib = bool(re.search(r"\b(eprint|archivePrefix)\b|arxiv\.org", entry["text"], re.IGNORECASE))
            if uses_arxiv_bib and int(assessment["has_formal_version"] or 0):
                flagged += 1
                print(
                    f"- key={entry['key']} tier={assessment['source_tier']} venue={assessment['canonical_venue'] or 'N/A'} "
                    f"doi={metadata.get('canonical_doi') or 'N/A'} url={metadata.get('canonical_url') or 'N/A'}"
                )

    if flagged == 0:
        print("No BibTeX entries require formal-version replacement.")
        return 0
    print(f"Flagged {flagged} BibTeX entr{'y' if flagged == 1 else 'ies'} that should prefer a formal version.")
    return 1 if args.fail_on_policy else 0


def normalize_section_lookup_map(content: str) -> dict[str, set[str]]:
    """Map normalized section paths to cited keys (including descendants)."""
    sections = extract_section_events(content)
    citations = extract_citation_commands(content)
    expanded: dict[str, set[str]] = {}
    for citation in citations:
        path = find_section_path_for_position(sections, int(citation["start"]))
        if not path:
            expanded.setdefault("", set()).update(citation["keys"])
            continue
        path_parts = [part.strip() for part in path.split(">") if part.strip()]
        for index in range(1, len(path_parts) + 1):
            ancestor = " > ".join(path_parts[:index])
            expanded.setdefault(normalize_text(ancestor), set()).update(citation["keys"])
    return expanded


def policy_threshold(policy: str, config: dict[str, Any]) -> tuple[float, float | None]:
    """Return the minimum A/B ratio and max C ratio for a source policy."""
    source_policy = config.get("source_policy") or {}
    if policy == "core":
        return float(source_policy.get("min_tier_ab_ratio_core", 0.8)), float(source_policy.get("max_tier_c_ratio_core", 0.2))
    if policy == "standard":
        return float(source_policy.get("min_tier_ab_ratio_standard", 0.6)), None
    return 0.0, None


def cmd_audit_tex(args: argparse.Namespace) -> int:
    tex_path = args.project_dir / "main.tex"
    if not tex_path.exists():
        print(f"error: main.tex not found in {args.project_dir}", file=sys.stderr)
        return 1

    config = load_paper_config(args.project_dir)
    issues = read_issue_rows(args.issues)
    citation_map = normalize_section_lookup_map(tex_path.read_text(encoding="utf-8"))

    failures = 0
    with connect(args.db) as conn:
        init_schema(conn)
        ensure_initialized(conn)
        ensure_policy_schema(conn)
        for issue in issues:
            if issue.get("Phase") != "Writing":
                continue
            section_path = normalize_text(issue.get("Section_Path") or "")
            source_policy = (issue.get("Source_Policy") or "").strip().lower()
            cited_keys = citation_map.get(section_path, set())
            if not cited_keys:
                print(f"- {issue['ID']}: no citations found for section path '{issue.get('Section_Path')}'")
                if args.fail_on_policy:
                    failures += 1
                continue

            tier_counts = {"A": 0, "B": 0, "C": 0, "unknown": 0}
            for key in sorted(cited_keys):
                row = conn.execute(
                    """
                    SELECT sa.source_tier
                    FROM citation_keys ck
                    LEFT JOIN source_assessments sa ON sa.work_id = ck.work_id
                    WHERE ck.key = ?;
                    """,
                    (key,),
                ).fetchone()
                if row is None or row["source_tier"] is None:
                    tier_counts["unknown"] += 1
                else:
                    tier_counts[str(row["source_tier"])] += 1

            total_known = tier_counts["A"] + tier_counts["B"] + tier_counts["C"]
            ab_ratio = ((tier_counts["A"] + tier_counts["B"]) / total_known) if total_known else 0.0
            c_ratio = (tier_counts["C"] / total_known) if total_known else 0.0
            min_ab_ratio, max_c_ratio = policy_threshold(source_policy, config)

            status = "PASS"
            if source_policy in {"core", "standard"} and ab_ratio < min_ab_ratio:
                status = "FAIL"
            if source_policy == "core" and max_c_ratio is not None and c_ratio > max_c_ratio:
                status = "FAIL"
            if source_policy == "frontier" and tier_counts["C"] > 0:
                status = "WARN"
            if status == "FAIL":
                failures += 1

            print(
                f"- {issue['ID']} [{status}] section={issue.get('Section_Path')} policy={source_policy} "
                f"A={tier_counts['A']} B={tier_counts['B']} C={tier_counts['C']} unknown={tier_counts['unknown']} "
                f"AB_ratio={ab_ratio:.2f} C_ratio={c_ratio:.2f}"
            )

    return 1 if failures and args.fail_on_policy else 0


def cmd_lint_bib(args: argparse.Namespace) -> int:
    """Lint ref.bib against main.tex for orphans, danglers, dupes, missing fields."""
    bib_path = args.project_dir / "ref.bib"
    tex_path = args.project_dir / "main.tex"
    if not bib_path.exists():
        print(f"error: ref.bib not found in {args.project_dir}", file=sys.stderr)
        return 1
    if not tex_path.exists():
        print(f"error: main.tex not found in {args.project_dir}", file=sys.stderr)
        return 1

    bib_content = bib_path.read_text(encoding="utf-8")
    entries = parse_bibtex_entries(bib_content)
    citation_info = count_citations(tex_path)
    cited_keys = set(citation_info["keys"])

    bib_keys: list[str] = []
    seen_keys: dict[str, int] = {}
    duplicates: list[str] = []
    for entry in entries:
        key = entry["key"]
        bib_keys.append(key)
        if key in seen_keys:
            duplicates.append(key)
        seen_keys[key] = seen_keys.get(key, 0) + 1

    bib_key_set = set(bib_keys)
    orphans = sorted(bib_key_set - cited_keys)
    danglers = sorted(cited_keys - bib_key_set)

    missing_title: list[str] = []
    missing_author: list[str] = []
    missing_year: list[str] = []
    article_like = {"article", "inproceedings", "conference", "incollection"}
    for entry in entries:
        if not re.search(r"title\s*=", entry["text"], re.IGNORECASE):
            missing_title.append(entry["key"])
        if entry["entry_type"].lower() in article_like:
            if not re.search(r"author\s*=", entry["text"], re.IGNORECASE):
                missing_author.append(entry["key"])
        if not re.search(r"year\s*=", entry["text"], re.IGNORECASE):
            missing_year.append(entry["key"])

    fails = 0
    warns = 0
    print(f"BibTeX lint: ref.bib ({len(entries)} entries) vs main.tex ({citation_info['unique']} unique citations)")
    if danglers:
        fails += len(danglers)
        print(f"- FAIL: {len(danglers)} dangling citation(s) (cited but not in bib): {', '.join(danglers)}")
    if orphans:
        warns += len(orphans)
        print(f"- WARN: {len(orphans)} orphan entry/entries (in bib but never cited): {', '.join(orphans)}")
    if duplicates:
        fails += len(duplicates)
        print(f"- FAIL: {len(duplicates)} duplicate key(s): {', '.join(sorted(set(duplicates)))}")
    if missing_title:
        warns += len(missing_title)
        print(f"- WARN: {len(missing_title)} entry/entries missing 'title' field: {', '.join(missing_title)}")
    if missing_author:
        warns += len(missing_author)
        print(f"- WARN: {len(missing_author)} entry/entries missing 'author' field: {', '.join(missing_author)}")
    if missing_year:
        warns += len(missing_year)
        print(f"- WARN: {len(missing_year)} entry/entries missing 'year' field: {', '.join(missing_year)}")
    print(f"Summary: {fails} FAIL, {warns} WARN")
    if fails > 0 and args.fail_on_lint:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recommend and audit citations using source policy.")
    parser.add_argument("--project-dir", required=True, help="Paper/project directory.")
    parser.add_argument("--db", help="Registry sqlite path. Defaults to <project-dir>/notes/arxiv-registry.sqlite3.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_recommend = sub.add_parser("recommend", help="Recommend citations for a single issue.")
    p_recommend.add_argument("--issues", required=True, type=Path, help="Path to issues CSV.")
    p_recommend.add_argument("--issue-id", required=True, help="Issue ID to recommend sources for.")
    p_recommend.add_argument("--search-id", type=int, help="Limit recommendations to a stored search result set.")
    p_recommend.add_argument("--arxiv-id", nargs="*", default=[], help="Optional extra arXiv IDs to include.")
    p_recommend.add_argument("--limit", type=int, default=10, help="Number of recommendations to print.")
    p_recommend.add_argument("--timeout-s", type=int, default=20, help="Network timeout in seconds.")
    p_recommend.add_argument("--refresh", action="store_true", help="Refresh source assessments before ranking.")
    p_recommend.set_defaults(fn=cmd_recommend)

    p_bib = sub.add_parser("audit-bib", help="Audit ref.bib for arXiv entries that should prefer formal versions.")
    p_bib.add_argument("--fail-on-policy", action="store_true", help="Return a non-zero exit code when policy violations are found.")
    p_bib.set_defaults(fn=cmd_audit_bib)

    p_tex = sub.add_parser("audit-tex", help="Audit main.tex citations against issues source policy.")
    p_tex.add_argument("--issues", required=True, type=Path, help="Path to issues CSV.")
    p_tex.add_argument("--fail-on-policy", action="store_true", help="Return a non-zero exit code when policy violations are found.")
    p_tex.set_defaults(fn=cmd_audit_tex)

    p_lint = sub.add_parser("lint-bib", help="Lint ref.bib for orphans, danglers, duplicates, and missing fields.")
    p_lint.add_argument("--fail-on-lint", action="store_true", help="Return non-zero exit code when lint issues are found.")
    p_lint.set_defaults(fn=cmd_lint_bib)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.project_dir = Path(args.project_dir).expanduser().resolve()
    args.db = Path(args.db).expanduser().resolve() if args.db else (args.project_dir / "notes" / "arxiv-registry.sqlite3").resolve()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
