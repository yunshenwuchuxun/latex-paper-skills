#!/usr/bin/env python3
"""Generate LaTeX tables from experiment result CSV files.

Usage:
    python3 generate_results_table.py <results.csv> -o <output.tex>
    python3 generate_results_table.py <results.csv> -o <output.tex> --bold-best --caption "Main results"
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


def read_results_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a result CSV and return (fieldnames, rows)."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def is_numeric(value: str) -> bool:
    """Check if a string represents a numeric value (possibly with ± std)."""
    cleaned = re.sub(r"[±\s]", " ", value).strip().split()[0]
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def parse_numeric(value: str) -> float:
    """Extract the main numeric value (ignoring ± std part)."""
    cleaned = re.sub(r"[±\s]", " ", value).strip().split()[0]
    return float(cleaned)


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in text."""
    replacements = [
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def bold_best_in_column(
    rows: list[dict[str, str]],
    col: str,
    higher_is_better: bool = True,
) -> dict[int, str]:
    """Find the best value in a column and return {row_index: formatted_value}.

    Values already containing \\textbf are skipped.
    """
    best_idx = -1
    best_val = float("-inf") if higher_is_better else float("inf")
    formatted: dict[int, str] = {}

    for i, row in enumerate(rows):
        val_str = row.get(col, "").strip()
        if not val_str or not is_numeric(val_str):
            formatted[i] = escape_latex(val_str)
            continue
        val = parse_numeric(val_str)
        formatted[i] = escape_latex(val_str)
        if higher_is_better and val > best_val:
            best_val = val
            best_idx = i
        elif not higher_is_better and val < best_val:
            best_val = val
            best_idx = i

    if best_idx >= 0:
        formatted[best_idx] = r"\textbf{" + formatted[best_idx] + "}"

    return formatted


def generate_latex_table(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    *,
    bold_best: bool = False,
    higher_is_better: bool = True,
    caption: str = "",
    label: str = "",
) -> str:
    """Generate a LaTeX table string from CSV data."""
    if not rows:
        return "% Empty result set\n"

    # Identify metric columns (numeric data)
    metric_cols: list[str] = []
    non_metric_cols: list[str] = []
    for col in fieldnames:
        if any(is_numeric(row.get(col, "")) for row in rows):
            metric_cols.append(col)
        else:
            non_metric_cols.append(col)

    # Determine display columns: skip internal columns
    skip = {"seed", "timestamp", "notes", "experiment_id"}
    display_cols = [c for c in fieldnames if c.lower() not in skip]

    # Bold best per metric column
    col_formats: dict[str, dict[int, str]] = {}
    for col in display_cols:
        if bold_best and col in metric_cols:
            col_formats[col] = bold_best_in_column(rows, col, higher_is_better)
        else:
            col_formats[col] = {i: escape_latex(row.get(col, "")) for i, row in enumerate(rows)}

    # Build LaTeX
    n_cols = len(display_cols)
    col_spec = "l" + "c" * (n_cols - 1)
    lines: list[str] = []

    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    if caption:
        lines.append(r"\caption{" + caption + "}")
    if label:
        lines.append(r"\label{" + label + "}")
    lines.append(r"\begin{tabular}{" + col_spec + "}")
    lines.append(r"\toprule")

    # Header
    header = " & ".join(escape_latex(c) for c in display_cols) + r" \\"
    lines.append(header)
    lines.append(r"\midrule")

    # Data rows
    for i in range(len(rows)):
        cells = [col_formats[col][i] for col in display_cols]
        lines.append(" & ".join(cells) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate LaTeX table from results CSV.")
    parser.add_argument("csv_file", type=Path, help="Input result CSV file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .tex file (default: stdout)")
    parser.add_argument("--bold-best", action="store_true", help="Bold the best value per metric column")
    parser.add_argument("--lower-is-better", action="store_true", help="Invert best direction (lower = better)")
    parser.add_argument("--caption", type=str, default="", help="Table caption")
    parser.add_argument("--label", type=str, default="", help="Table label (e.g., tab:main)")
    args = parser.parse_args()

    if not args.csv_file.exists():
        print(f"File not found: {args.csv_file}", file=sys.stderr)
        return 1

    fieldnames, rows = read_results_csv(args.csv_file)
    if not fieldnames:
        print("CSV has no columns.", file=sys.stderr)
        return 1

    latex = generate_latex_table(
        fieldnames,
        rows,
        bold_best=args.bold_best,
        higher_is_better=not args.lower_is_better,
        caption=args.caption,
        label=args.label,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(latex, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(latex)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
