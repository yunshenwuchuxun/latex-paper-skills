#!/usr/bin/env python3
"""
Sync ref.bib entries into notes/arxiv-registry.sqlite3 for source-tier QA.

Why:
- citation_policy.py audit-tex expects BibTeX keys to be mapped to work_ids via the
  registry table `citation_keys`, and expects `source_assessments` to exist for
  those works.
- Our ref.bib is generated from Crossref DOIs (not arXiv-first), so the registry
  may not contain corresponding works/citation key mappings.

What this script does:
- Parses ref.bib.
- For each entry, finds or creates a registry `works` row:
  - If DOI exists: use existing `works` row with that DOI; otherwise create one
    with a synthetic arxiv_id `doi:<DOI>`.
  - If DOI missing: create/find a synthetic work with arxiv_id `bib:<cite_key>`.
- Upserts `citation_keys` so BibTeX keys resolve to work_ids.

After running, execute:
  python .codex/skills/arxiv-paper-writer/scripts/source_ranker.py --project-dir <paper_dir> rank
  python .codex/skills/arxiv-paper-writer/scripts/citation_policy.py --project-dir <paper_dir> audit-tex --issues <issues.csv> --fail-on-policy
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / ".codex" / "skills").exists():
            return parent
    raise RuntimeError(f"Could not locate repo root from: {start}")


def safe_slug(value: str) -> str:
    return (value or "").strip().replace("\n", " ").replace("\r", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync ref.bib citation keys into arXiv registry DB.")
    parser.add_argument("--paper-dir", type=Path, required=True, help="Paper directory containing ref.bib and notes/.")
    args = parser.parse_args()

    paper_dir = args.paper_dir.expanduser().resolve()
    bib_path = paper_dir / "ref.bib"
    db_path = paper_dir / "notes" / "arxiv-registry.sqlite3"
    if not bib_path.exists():
        print(f"error: ref.bib not found: {bib_path}", file=sys.stderr)
        return 1

    repo_root = find_repo_root(Path(__file__).resolve())
    shared_dir = repo_root / ".codex" / "skills" / "_shared"
    scripts_dir = repo_root / ".codex" / "skills" / "arxiv-paper-writer" / "scripts"
    sys.path.insert(0, str(shared_dir))
    sys.path.insert(0, str(scripts_dir))

    # Imports resolved via sys.path above.
    from arxiv_registry import connect, ensure_initialized, init_schema  # type: ignore
    from paper_utils import extract_bibtex_field, now_iso, parse_bibtex_entries  # type: ignore
    from source_policy_utils import normalize_doi  # type: ignore

    bib_entries = parse_bibtex_entries(bib_path.read_text(encoding="utf-8"))

    with connect(db_path) as conn:
        init_schema(conn)
        ensure_initialized(conn)

        inserted_works = 0
        updated_keys = 0
        skipped = 0

        for entry in bib_entries:
            cite_key = (entry.get("key") or "").strip()
            if not cite_key:
                skipped += 1
                continue

            text = str(entry.get("text") or "")
            title = safe_slug(extract_bibtex_field(text, "title") or cite_key)
            year = safe_slug(extract_bibtex_field(text, "year") or "")
            doi = normalize_doi(extract_bibtex_field(text, "doi"))
            url = safe_slug(extract_bibtex_field(text, "url") or "")
            journal = safe_slug(extract_bibtex_field(text, "journal") or "")
            booktitle = safe_slug(extract_bibtex_field(text, "booktitle") or "")
            journal_ref = journal or booktitle or ""

            now = now_iso()

            work_id: int | None = None
            if doi:
                row = conn.execute("SELECT work_id FROM works WHERE doi = ?;", (doi,)).fetchone()
                if row is not None:
                    work_id = int(row["work_id"])
                else:
                    synthetic_arxiv_id = f"doi:{doi}"
                    conn.execute(
                        """
                        INSERT INTO works(
                          arxiv_id, title, summary, published, updated, comment,
                          primary_category, categories_json, abs_url, pdf_url,
                          journal_ref, doi, created_at, last_seen_at
                        )
                        VALUES(?, ?, NULL, ?, NULL, NULL, NULL, NULL, ?, NULL, ?, ?, ?, ?);
                        """,
                        (
                            synthetic_arxiv_id,
                            title,
                            year or None,
                            url or None,
                            journal_ref or None,
                            doi,
                            now,
                            now,
                        ),
                    )
                    work_id = int(conn.execute("SELECT work_id FROM works WHERE arxiv_id = ?;", (synthetic_arxiv_id,)).fetchone()["work_id"])
                    inserted_works += 1
            else:
                synthetic_arxiv_id = f"bib:{cite_key}"
                row = conn.execute("SELECT work_id FROM works WHERE arxiv_id = ?;", (synthetic_arxiv_id,)).fetchone()
                if row is not None:
                    work_id = int(row["work_id"])
                else:
                    conn.execute(
                        """
                        INSERT INTO works(
                          arxiv_id, title, summary, published, updated, comment,
                          primary_category, categories_json, abs_url, pdf_url,
                          journal_ref, doi, created_at, last_seen_at
                        )
                        VALUES(?, ?, NULL, ?, NULL, NULL, NULL, NULL, ?, NULL, ?, NULL, ?, ?);
                        """,
                        (
                            synthetic_arxiv_id,
                            title,
                            year or None,
                            url or None,
                            journal_ref or None,
                            now,
                            now,
                        ),
                    )
                    work_id = int(conn.execute("SELECT work_id FROM works WHERE arxiv_id = ?;", (synthetic_arxiv_id,)).fetchone()["work_id"])
                    inserted_works += 1

            if work_id is None:
                skipped += 1
                continue

            # Ensure citation_keys points from cite_key -> work_id.
            # citation_keys.key is UNIQUE, so guard against conflicts.
            existing_by_key = conn.execute("SELECT work_id FROM citation_keys WHERE key = ?;", (cite_key,)).fetchone()
            if existing_by_key is not None and int(existing_by_key["work_id"]) != work_id:
                print(
                    f"warning: cite key already mapped to different work_id; skip key={cite_key} "
                    f"current={int(existing_by_key['work_id'])} new={work_id}",
                    file=sys.stderr,
                )
                skipped += 1
                continue

            existing_row = conn.execute("SELECT work_id, key FROM citation_keys WHERE work_id = ?;", (work_id,)).fetchone()
            if existing_row is None:
                conn.execute(
                    "INSERT INTO citation_keys(work_id, key, base_key, generated_at) VALUES(?, ?, ?, ?);",
                    (work_id, cite_key, cite_key, now),
                )
                updated_keys += 1
            else:
                if (existing_row["key"] or "") != cite_key:
                    conn.execute(
                        "UPDATE citation_keys SET key = ?, base_key = ?, generated_at = ? WHERE work_id = ?;",
                        (cite_key, cite_key, now, work_id),
                    )
                    updated_keys += 1

            # Keep the works row minimally informative (idempotent).
            conn.execute(
                """
                UPDATE works
                SET title = COALESCE(NULLIF(title, ''), ?),
                    published = COALESCE(published, ?),
                    abs_url = COALESCE(abs_url, ?),
                    journal_ref = COALESCE(journal_ref, ?),
                    last_seen_at = ?
                WHERE work_id = ?;
                """,
                (title, year or None, url or None, journal_ref or None, now, work_id),
            )

        conn.commit()

    print(f"Synced {len(bib_entries)} BibTeX entries.")
    print(f"- inserted works: {inserted_works}")
    print(f"- upserted citation_keys: {updated_keys}")
    print(f"- skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

