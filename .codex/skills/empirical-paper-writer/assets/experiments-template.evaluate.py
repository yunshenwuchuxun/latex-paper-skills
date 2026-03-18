#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from train import train_one


def run_experiment(*, row: Any, cfg: dict[str, Any], results_dir: Path) -> None:
    """
    Execute a single experiment row.

    TODO: Replace this scaffold logic with your real training/evaluation pipeline.

    Contract:
    - Write *verified* results only. Do not fabricate numbers.
    - Each output row should be traceable to experiment_id + dataset + variant.
    """
    artifacts = train_one(cfg, dataset_name=row.dataset, variant=row.our_method_variant)
    raise NotImplementedError(
        "Implement evaluation in evaluate.run_experiment() before executing experiments. "
        f"(trained checkpoint would be at {artifacts.checkpoint_path})"
    )

