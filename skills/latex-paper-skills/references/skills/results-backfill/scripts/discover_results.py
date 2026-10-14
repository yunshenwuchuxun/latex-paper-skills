#!/usr/bin/env python3
"""Discover experiment result files and match them to experiment-matrix rows.

Usage:
    python3 discover_results.py --project-dir <paper_dir>
    python3 discover_results.py --project-dir <paper_dir> --update-status
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# File-to-type matching
# ---------------------------------------------------------------------------

TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"^main_results", "main_comparison"),
    (r"^ablation", "ablation"),
    (r"^robustness", "robustness"),
    (r"^efficiency", "efficiency"),
]


def infer_experiment_type(filename: str) -> str | None:
    """Infer experiment type from a result filename."""
    stem = Path(filename).stem.lower()
    for pattern, exp_type in TYPE_PATTERNS:
        if re.match(pattern, stem):
            return exp_type
    return None


# ---------------------------------------------------------------------------
# experiment-matrix I/O
# ---------------------------------------------------------------------------

def read_experiment_matrix(path: Path) -> list[dict[str, str]]:
    """Read experiment-matrix.csv rows."""
    if not path.exists():
        raise SystemExit(f"experiment-matrix.csv not found: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def write_experiment_matrix(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    """Write rows back to experiment-matrix.csv."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def scan_results(results_dir: Path) -> list[Path]:
    """Collect CSV and JSON result files from the results directory."""
    if not results_dir.is_dir():
        return []
    return sorted(
        p for p in results_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".csv", ".json"}
    )


def match_files_to_matrix(
    result_files: list[Path],
    matrix_rows: list[dict[str, str]],
) -> dict[str, list[Path]]:
    """Match result files to experiment-matrix rows by experiment_id or type.

    Returns a mapping from ``experiment_id`` to a list of matched file paths.
    A file matches if:
      1. Its stem starts with the experiment_id (case-insensitive), OR
      2. The ``output_file`` column (if present) matches the file name, OR
      3. The inferred type from the filename matches the row's ``type`` column.
    """
    matched: dict[str, list[Path]] = {row["experiment_id"]: [] for row in matrix_rows}

    for fpath in result_files:
        stem_lower = fpath.stem.lower()
        fname_lower = fpath.name.lower()
        inferred = infer_experiment_type(fpath.name)

        for row in matrix_rows:
            eid = row["experiment_id"]
            eid_lower = eid.lower().replace("-", "_")

            # Match by experiment_id prefix
            if stem_lower.startswith(eid_lower):
                matched[eid].append(fpath)
                continue

            # Match by explicit output_file column
            output_file = row.get("output_file", "").strip()
            if output_file and fname_lower == output_file.lower():
                matched[eid].append(fpath)
                continue

            # Match by inferred type
            if inferred and inferred == row.get("type", "").strip():
                # Only auto-match by type if there is a single row of that type
                # or if the dataset appears in the filename
                dataset = row.get("dataset", "").strip().lower().replace(" ", "_")
                if dataset and dataset in stem_lower:
                    matched[eid].append(fpath)

    return matched


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def build_report(
    matrix_rows: list[dict[str, str]],
    matches: dict[str, list[Path]],
) -> dict:
    """Build a JSON-serializable discovery report."""
    verified = []
    missing = []
    for row in matrix_rows:
        eid = row["experiment_id"]
        files = matches.get(eid, [])
        entry = {
            "experiment_id": eid,
            "type": row.get("type", ""),
            "dataset": row.get("dataset", ""),
            "current_status": row.get("result_status", ""),
        }
        if files:
            entry["matched_files"] = [str(f.name) for f in files]
            verified.append(entry)
        else:
            missing.append(entry)

    return {
        "total_experiments": len(matrix_rows),
        "verified": len(verified),
        "missing": len(missing),
        "verified_experiments": verified,
        "missing_experiments": missing,
    }


def print_report(report: dict) -> None:
    """Print a human-readable discovery summary."""
    total = report["total_experiments"]
    v = report["verified"]
    m = report["missing"]
    print(f"Results discovered: {v}/{total} experiments verified")
    if report["missing_experiments"]:
        print(f"Missing ({m}):")
        for exp in report["missing_experiments"]:
            print(f"  - {exp['experiment_id']} ({exp['type']}, {exp['dataset']})")
    if report["verified_experiments"]:
        print(f"\nMatched ({v}):")
        for exp in report["verified_experiments"]:
            files = ", ".join(exp["matched_files"])
            print(f"  - {exp['experiment_id']} -> {files}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Discover and match experiment results.")
    parser.add_argument("--project-dir", type=Path, required=True, help="Paper project root")
    parser.add_argument(
        "--matrix",
        type=Path,
        default=None,
        help="Path to experiment-matrix.csv (default: <project-dir>/notes/design/experiment-matrix.csv)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Path to results directory (default: <project-dir>/paper/results)",
    )
    parser.add_argument("--update-status", action="store_true", help="Update result_status in experiment-matrix.csv")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    args = parser.parse_args()

    project_dir: Path = args.project_dir.resolve()
    matrix_path = args.matrix or project_dir / "notes" / "design" / "experiment-matrix.csv"
    results_dir = args.results_dir or project_dir / "paper" / "results"

    matrix_rows = read_experiment_matrix(matrix_path)
    if not matrix_rows:
        print("experiment-matrix.csv is empty.", file=sys.stderr)
        return 1

    result_files = scan_results(results_dir)
    matches = match_files_to_matrix(result_files, matrix_rows)
    report = build_report(matrix_rows, matches)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if args.update_status:
        fieldnames = list(matrix_rows[0].keys())
        changed = 0
        for row in matrix_rows:
            eid = row["experiment_id"]
            if matches.get(eid) and row.get("result_status", "").strip() != "verified":
                row["result_status"] = "verified"
                changed += 1
        if changed:
            write_experiment_matrix(matrix_path, matrix_rows, fieldnames)
            print(f"\nUpdated {changed} row(s) to result_status=verified in {matrix_path.name}")

    return 0 if report["missing"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
