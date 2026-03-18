#!/usr/bin/env python3
"""Validate empirical paper design CSVs (experiment-matrix, baselines, method-components).

Usage:
    python3 validate_design_csvs.py --project-dir <paper_dir>
    python3 validate_design_csvs.py --project-dir <paper_dir> --fail-on-issues
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Expected schemas
# ---------------------------------------------------------------------------

EXPERIMENT_MATRIX_REQUIRED = [
    "experiment_id", "type", "claim_id", "dataset", "metric",
    "baselines_involved", "our_method_variant", "expected_outcome",
    "result_status", "notes",
]
EXPERIMENT_MATRIX_STATUS_VALUES = {"planned", "placeholder", "verified"}

BASELINES_REQUIRED = [
    "name", "paper_title", "arxiv_id", "code_url", "category",
    "datasets_tested", "metrics_reported", "strengths", "weaknesses",
    "selected", "selection_reason",
]
BASELINES_SELECTED_VALUES = {"yes", "no"}

METHOD_COMPONENTS_REQUIRED = [
    "component_id", "name", "role", "input_format", "output_format",
    "is_novel", "replaceable_by", "ablation_priority", "notes",
]
METHOD_COMPONENTS_NOVEL_VALUES = {"yes", "no"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV file, return (fieldnames, rows)."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fieldnames = [f.strip() for f in (reader.fieldnames or [])]
        rows = list(reader)
    return fieldnames, rows


def check_columns(
    filename: str,
    actual: list[str],
    expected: list[str],
) -> list[str]:
    """Check that all expected columns exist."""
    actual_lower = {c.lower() for c in actual}
    errors: list[str] = []
    for col in expected:
        if col.lower() not in actual_lower:
            errors.append(f"{filename}: missing column '{col}'")
    return errors


def check_enum(
    filename: str,
    rows: list[dict[str, str]],
    column: str,
    allowed: set[str],
) -> list[str]:
    """Check that values in a column are within the allowed set."""
    errors: list[str] = []
    col_key = None
    if rows:
        for k in rows[0]:
            if k.strip().lower() == column.lower():
                col_key = k
                break
    if col_key is None:
        return []

    for i, row in enumerate(rows, start=2):  # row 1 is header
        val = (row.get(col_key) or "").strip().lower()
        if val and val not in allowed:
            errors.append(f"{filename} row {i}: {column}='{val}' not in {sorted(allowed)}")
    return errors


def check_non_empty(
    filename: str,
    rows: list[dict[str, str]],
    columns: list[str],
) -> list[str]:
    """Check that key columns are not empty."""
    errors: list[str] = []
    for i, row in enumerate(rows, start=2):
        for col in columns:
            col_key = None
            for k in row:
                if k.strip().lower() == col.lower():
                    col_key = k
                    break
            if col_key and not (row.get(col_key) or "").strip():
                errors.append(f"{filename} row {i}: '{col}' is empty")
    return errors


# ---------------------------------------------------------------------------
# Per-file validators
# ---------------------------------------------------------------------------

def validate_experiment_matrix(path: Path) -> list[str]:
    """Validate experiment-matrix.csv."""
    if not path.exists():
        return [f"experiment-matrix.csv not found: {path}"]
    fieldnames, rows = read_csv(path)
    errors = check_columns("experiment-matrix.csv", fieldnames, EXPERIMENT_MATRIX_REQUIRED)
    if errors:
        return errors
    errors.extend(check_enum("experiment-matrix.csv", rows, "result_status", EXPERIMENT_MATRIX_STATUS_VALUES))
    errors.extend(check_non_empty("experiment-matrix.csv", rows, ["experiment_id", "type", "claim_id"]))
    # Check uniqueness of experiment_id
    ids = [(row.get("experiment_id") or "").strip() for row in rows]
    seen: set[str] = set()
    for eid in ids:
        if eid in seen:
            errors.append(f"experiment-matrix.csv: duplicate experiment_id '{eid}'")
        seen.add(eid)
    if not rows:
        errors.append("experiment-matrix.csv: no data rows")
    return errors


def validate_baselines(path: Path) -> list[str]:
    """Validate baselines.csv."""
    if not path.exists():
        return [f"baselines.csv not found: {path}"]
    fieldnames, rows = read_csv(path)
    errors = check_columns("baselines.csv", fieldnames, BASELINES_REQUIRED)
    if errors:
        return errors
    errors.extend(check_enum("baselines.csv", rows, "selected", BASELINES_SELECTED_VALUES))
    errors.extend(check_non_empty("baselines.csv", rows, ["name", "category"]))
    if not rows:
        errors.append("baselines.csv: no data rows")
    return errors


def validate_method_components(path: Path) -> list[str]:
    """Validate method-components.csv."""
    if not path.exists():
        return [f"method-components.csv not found: {path}"]
    fieldnames, rows = read_csv(path)
    errors = check_columns("method-components.csv", fieldnames, METHOD_COMPONENTS_REQUIRED)
    if errors:
        return errors
    errors.extend(check_enum("method-components.csv", rows, "is_novel", METHOD_COMPONENTS_NOVEL_VALUES))
    errors.extend(check_non_empty("method-components.csv", rows, ["component_id", "name", "role"]))
    # At least one novel component
    has_novel = any(
        (row.get("is_novel") or "").strip().lower() == "yes"
        for row in rows
    )
    if rows and not has_novel:
        errors.append("method-components.csv: no component marked is_novel=yes")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate empirical paper design CSVs.")
    parser.add_argument("--project-dir", type=Path, required=True, help="Paper project root")
    parser.add_argument("--fail-on-issues", action="store_true", help="Exit 1 on any validation issue")
    args = parser.parse_args()

    project_dir: Path = args.project_dir.resolve()
    design_dir = project_dir / "notes" / "design"

    all_errors: list[str] = []

    all_errors.extend(validate_experiment_matrix(design_dir / "experiment-matrix.csv"))
    all_errors.extend(validate_baselines(design_dir / "baselines.csv"))
    all_errors.extend(validate_method_components(design_dir / "method-components.csv"))

    if all_errors:
        for err in all_errors:
            print(f"  issue: {err}", file=sys.stderr)
        print(f"\n{len(all_errors)} validation issue(s) found.", file=sys.stderr)
        if args.fail_on_issues:
            return 1
    else:
        print("All design CSVs validated successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
