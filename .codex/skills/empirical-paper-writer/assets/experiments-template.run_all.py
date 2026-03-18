#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from utils.config import load_yaml
from utils.paths import resolve_project_path


@dataclass(frozen=True)
class ExperimentRow:
    experiment_id: str
    type: str
    claim_id: str
    dataset: str
    metric: str
    baselines_involved: str
    our_method_variant: str
    expected_outcome: str
    result_status: str
    notes: str


def read_experiment_matrix(path: Path) -> list[ExperimentRow]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[ExperimentRow] = []
        for raw in reader:
            rows.append(
                ExperimentRow(
                    experiment_id=(raw.get("experiment_id") or "").strip(),
                    type=(raw.get("type") or "").strip(),
                    claim_id=(raw.get("claim_id") or "").strip(),
                    dataset=(raw.get("dataset") or "").strip(),
                    metric=(raw.get("metric") or "").strip(),
                    baselines_involved=(raw.get("baselines_involved") or "").strip(),
                    our_method_variant=(raw.get("our_method_variant") or "").strip(),
                    expected_outcome=(raw.get("expected_outcome") or "").strip(),
                    result_status=(raw.get("result_status") or "").strip(),
                    notes=(raw.get("notes") or "").strip(),
                )
            )
    return rows


def filter_rows(rows: Iterable[ExperimentRow], *, exp_type: str) -> list[ExperimentRow]:
    if not exp_type:
        return list(rows)
    return [r for r in rows if r.type == exp_type]


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestrate experiments defined in the experiment-matrix CSV.")
    parser.add_argument("--config", required=True, help="Path to YAML config (e.g., configs/default.yaml).")
    parser.add_argument(
        "--type",
        default="",
        help="Optional experiment type filter: main_comparison|ablation|robustness|efficiency",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would run (recommended until train/eval TODOs are implemented).",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    cfg = load_yaml(config_path)

    matrix_csv = Path(
        resolve_project_path(
            base_dir=config_path.parent,
            relative_path=str(cfg["paths"]["experiment_matrix_csv"]),
        )
    )
    rows = read_experiment_matrix(matrix_csv)
    selected = filter_rows(rows, exp_type=args.type)

    if not selected:
        print("No experiments matched the filter.")
        return 0

    print(f"Experiment matrix: {matrix_csv}")
    print(f"Selected experiments: {len(selected)}")
    for row in selected:
        print(
            f"- {row.experiment_id} [{row.type}] dataset={row.dataset} metric={row.metric} variant={row.our_method_variant}"
        )

    if args.dry_run:
        print("Dry-run only. No experiments executed; no results written.")
        return 0

    # Execution requires implementing train/evaluate TODOs.
    from evaluate import run_experiment  # noqa: WPS433 (local import for clearer error surfacing)

    results_dir = Path(
        resolve_project_path(
            base_dir=config_path.parent,
            relative_path=str(cfg["paths"]["results_dir"]),
        )
    )
    os.makedirs(results_dir, exist_ok=True)

    for row in selected:
        run_experiment(row=row, cfg=cfg, results_dir=results_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

