#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrainArtifacts:
    checkpoint_path: str
    extra: dict[str, Any]


def train_one(config: dict[str, Any], *, dataset_name: str, variant: str) -> TrainArtifacts:
    """
    TODO: Implement the actual training loop.

    Requirements for the scaffold:
    - deterministic seeding driven by config
    - save a checkpoint to a deterministic path
    - return the checkpoint path for evaluation
    """
    raise NotImplementedError("Implement training in train_one() before executing experiments.")

