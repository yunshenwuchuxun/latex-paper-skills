from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class MPCSolution:
    release_plan: Any  # np.ndarray shape (H,)
    expected_objective: float


def _simulate_storage_path(
    *,
    s0_mcm: float,
    q_m3s: Any,
    r_m3s: Any,
    m3s_to_mcm_per_day: float,
    loss_mcm_per_day: float,
):
    import numpy as np

    q = np.asarray(q_m3s, dtype=float).reshape(-1)
    r = np.asarray(r_m3s, dtype=float).reshape(-1)
    H = int(q.shape[0])
    s = np.zeros((H + 1,), dtype=float)
    s[0] = float(s0_mcm)
    delta = float(m3s_to_mcm_per_day)
    loss = float(loss_mcm_per_day)
    for h in range(H):
        s[h + 1] = s[h] + (q[h] - r[h]) * delta - loss
    return s


def _objective_expected(
    r_flat,
    *,
    s0_mcm: float,
    q_scenarios_m3s: Any,
    r_prev_m3s: float,
    s_bounds_mcm: Tuple[float, float],
    s_target_mcm: float,
    m3s_to_mcm_per_day: float,
    loss_mcm_per_day: float,
    weights: Dict[str, float],
):
    import numpy as np

    r = np.asarray(r_flat, dtype=float).reshape(-1)
    q_scen = np.asarray(q_scenarios_m3s, dtype=float)
    S, H = q_scen.shape

    w_s = float(weights.get("w_storage", 1.0))
    w_r = float(weights.get("w_release", 0.0))
    w_dr = float(weights.get("w_delta_release", 0.0))
    w_v = float(weights.get("w_violation", 0.0))

    s_lo, s_hi = float(s_bounds_mcm[0]), float(s_bounds_mcm[1])
    s_tgt = float(s_target_mcm)

    # Smoothness term
    dr0 = r[0] - float(r_prev_m3s)
    dr = np.diff(r, prepend=r[0])
    # Use dr[0]=0, then separately handle dr0 relative to prev release.
    dr[0] = dr0

    total = 0.0
    for s in range(S):
        stor = _simulate_storage_path(
            s0_mcm=s0_mcm,
            q_m3s=q_scen[s],
            r_m3s=r,
            m3s_to_mcm_per_day=m3s_to_mcm_per_day,
            loss_mcm_per_day=loss_mcm_per_day,
        )
        # stage cost uses storage at next step (post-action) to reflect constraints.
        stor_next = stor[1:]
        viol = np.maximum(0.0, stor_next - s_hi) ** 2 + np.maximum(0.0, s_lo - stor_next) ** 2
        stage = w_s * (stor_next - s_tgt) ** 2 + w_r * (r ** 2) + w_dr * (dr ** 2) + w_v * viol
        total += float(np.sum(stage))
    return total / float(S)


def solve_mpc_release_plan(
    *,
    s0_mcm: float,
    q_scenarios_m3s: Any,
    r_prev_m3s: float,
    s_bounds_mcm: Tuple[float, float],
    r_bounds_m3s: Tuple[float, float],
    s_target_mcm: float,
    m3s_to_mcm_per_day: float,
    loss_mcm_per_day: float,
    weights: Dict[str, float],
    maxiter: int = 100,
) -> MPCSolution:
    """
    Scenario-based MPC with soft storage constraints and box-bounded releases.
    """
    import numpy as np
    from scipy.optimize import minimize

    q_scen = np.asarray(q_scenarios_m3s, dtype=float)
    if q_scen.ndim != 2:
        raise ValueError("q_scenarios_m3s must be a 2D array [S,H].")
    S, H = q_scen.shape
    if H < 1:
        raise ValueError("Horizon must be >= 1.")

    r_lo, r_hi = float(r_bounds_m3s[0]), float(r_bounds_m3s[1])
    bounds = [(r_lo, r_hi) for _ in range(H)]

    # Initialization: hold previous release, clipped to bounds.
    x0 = np.full((H,), float(np.clip(r_prev_m3s, r_lo, r_hi)), dtype=float)

    def fun(x):
        return _objective_expected(
            x,
            s0_mcm=float(s0_mcm),
            q_scenarios_m3s=q_scen,
            r_prev_m3s=float(r_prev_m3s),
            s_bounds_mcm=(float(s_bounds_mcm[0]), float(s_bounds_mcm[1])),
            s_target_mcm=float(s_target_mcm),
            m3s_to_mcm_per_day=float(m3s_to_mcm_per_day),
            loss_mcm_per_day=float(loss_mcm_per_day),
            weights=dict(weights),
        )

    res = minimize(
        fun,
        x0,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": int(maxiter), "ftol": 1e-9},
    )

    r_opt = np.asarray(res.x, dtype=float).reshape(-1)
    return MPCSolution(release_plan=r_opt, expected_objective=float(res.fun))
