from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class Bounds:
    storage_mcm: Tuple[float, float]
    release_m3s: Tuple[float, float]
    target_storage_mcm: float
    loss_mcm_per_day: float


@dataclass(frozen=True)
class OpsTrace:
    dates: Any  # list[pd.Timestamp]
    storage_mcm: Any  # np.ndarray shape (T+1,)
    release_m3s: Any  # np.ndarray shape (T,)
    inflow_m3s: Any  # np.ndarray shape (T,)
    stage_cost: Any  # np.ndarray shape (T,)
    violation: Any  # np.ndarray shape (T,) bool


def estimate_bounds_and_loss(
    *,
    df,
    train_end: str,
    m3s_to_mcm_per_day: float,
    storage_quantiles: Tuple[float, float],
    release_quantiles: Tuple[float, float],
) -> Bounds:
    """
    Derive simple operational bounds from the training period.
    """
    import numpy as np
    import pandas as pd

    d = df.copy()
    d.index = pd.to_datetime(d.index)
    train = d[d.index <= pd.Timestamp(train_end)].copy()
    if train.shape[0] < 10:
        raise ValueError("Training window too small to estimate bounds.")

    s_lo, s_hi = [float(train["storage"].quantile(q)) for q in storage_quantiles]
    r_lo, r_hi = [float(train["outflow"].quantile(q)) for q in release_quantiles]
    s_tgt = float(train["storage"].median())

    # Estimate an unmodeled loss term to reduce storage drift:
    # loss_t = s_t + (q_t - r_t)*conv - s_{t+1}.
    conv = float(m3s_to_mcm_per_day)
    s = train["storage"].values.astype(float)
    q = train["inflow"].values.astype(float)
    r = train["outflow"].values.astype(float)
    if s.shape[0] < 2:
        loss = 0.0
    else:
        pred_next = s[:-1] + (q[:-1] - r[:-1]) * conv
        loss_series = pred_next - s[1:]
        loss = float(np.median(loss_series))
        if not np.isfinite(loss):
            loss = 0.0
        # Loss should not be negative on average; clamp for stability.
        loss = float(max(0.0, loss))

    return Bounds(
        storage_mcm=(float(s_lo), float(s_hi)),
        release_m3s=(float(r_lo), float(r_hi)),
        target_storage_mcm=float(s_tgt),
        loss_mcm_per_day=float(loss),
    )


def compute_ops_metrics(trace: OpsTrace, *, storage_bounds_mcm: Tuple[float, float]) -> Dict[str, float]:
    import numpy as np

    viol = np.asarray(trace.violation, dtype=bool)
    stage_cost = np.asarray(trace.stage_cost, dtype=float)
    storage = np.asarray(trace.storage_mcm, dtype=float)
    s_lo, s_hi = float(storage_bounds_mcm[0]), float(storage_bounds_mcm[1])

    viol_rate = float(np.mean(viol.astype(float))) if viol.size else float("nan")
    reliability = float(1.0 - viol_rate) if np.isfinite(viol_rate) else float("nan")

    # Vulnerability = mean normalized violation magnitude when failing.
    if np.any(viol):
        s_next = storage[1:]
        mag = np.maximum(0.0, s_next - s_hi) + np.maximum(0.0, s_lo - s_next)
        vuln = float(np.mean(mag[viol])) / float(max(1e-9, (s_hi - s_lo)))
    else:
        vuln = 0.0

    obj = float(np.mean(stage_cost)) if stage_cost.size else float("nan")
    return {
        "violation_rate": viol_rate,
        "objective": obj,
        "reliability": reliability,
        "vulnerability": float(vuln),
    }

