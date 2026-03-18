from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from dispatch.mpc import solve_mpc_release_plan
from forecast.ar import (
    ar_feature_from_hist,
    ar_multistep_forecast_mean,
    fit_ar_ridge,
    rls_init,
    rls_update,
)


@dataclass(frozen=True)
class RolloutVariant:
    name: str
    rolling_calibration: bool
    scenario_mpc: bool
    feedback_inflation: bool
    point_forecast_only: bool = False


@dataclass(frozen=True)
class Timing:
    calib_s: float
    dispatch_s: float
    total_s: float


@dataclass(frozen=True)
class RolloutSummary:
    metrics: Dict[str, float]
    timing: Timing


def _stage_cost(
    *,
    s_next_mcm: float,
    r_m3s: float,
    r_prev_m3s: float,
    bounds_mcm: Tuple[float, float],
    target_mcm: float,
    weights: Dict[str, float],
):
    import numpy as np

    w_s = float(weights.get("w_storage", 1.0))
    w_r = float(weights.get("w_release", 0.0))
    w_dr = float(weights.get("w_delta_release", 0.0))
    w_v = float(weights.get("w_violation", 0.0))

    s_lo, s_hi = float(bounds_mcm[0]), float(bounds_mcm[1])
    viol = float(max(0.0, s_next_mcm - s_hi) ** 2 + max(0.0, s_lo - s_next_mcm) ** 2)
    dr = float(r_m3s - r_prev_m3s)
    return float(w_s * (s_next_mcm - target_mcm) ** 2 + w_r * (r_m3s ** 2) + w_dr * (dr ** 2) + w_v * viol)


def simulate_closed_loop_ar_mpc(
    *,
    df,
    variant: RolloutVariant,
    ar_order: int,
    forgetting_factor: float,
    init_ridge: float,
    sigma_ewma_alpha: float,
    horizon_days: int,
    scenario_count: int,
    m3s_to_mcm_per_day: float,
    bounds_storage_mcm: Tuple[float, float],
    bounds_release_m3s: Tuple[float, float],
    target_storage_mcm: float,
    loss_mcm_per_day: float,
    dispatch_weights: Dict[str, float],
    feedback_cfg: Dict[str, float],
    train_end: str,
    tune_end: str,
    test_end: str,
    rng,
    inflow_scale_alpha: float = 1.0,
    obs_missing_rate: float = 0.0,
    obs_delay_days: int = 0,
) -> RolloutSummary:
    """
    End-to-end closed-loop simulation using an AR(p) forecast and (scenario) MPC dispatch.

    The decision at day t uses inflow observations up to day t-1 (causal).
    """
    import numpy as np
    import pandas as pd
    import time

    d = df.copy()
    d.index = pd.to_datetime(d.index)
    d = d.sort_index()

    # Apply a synthetic regime-shift scaling to inflow/outflow only through inflow (physical forcing).
    inflow = d["inflow"].values.astype(float) * float(inflow_scale_alpha)
    dates = d.index.to_pydatetime()

    # Fit static AR on training period for both static and rolling variants.
    train_mask = d.index <= pd.Timestamp(train_end)
    tune_mask = (d.index > pd.Timestamp(train_end)) & (d.index <= pd.Timestamp(tune_end))
    test_mask = (d.index > pd.Timestamp(tune_end)) & (d.index <= pd.Timestamp(test_end))

    y_train = inflow[train_mask]
    theta_static, _, sigma_static = fit_ar_ridge(y_train, order=int(ar_order), ridge=1e-3)

    # Rolling state (warm up through tuning period so test starts stable).
    rls = rls_init(order=int(ar_order), init_ridge=float(init_ridge), theta0=theta_static, sigma0=float(sigma_static))
    # Feedback inflation state: fast EWMA of squared one-step errors.
    infl_alpha = float(feedback_cfg.get("inflation_ewma_alpha", 0.95))
    infl_max = float(feedback_cfg.get("inflation_max", 3.0))
    err2_fast = float(rls.sigma2_ewma)
    last_mu1 = None  # predicted inflow for current day (from yesterday)

    # Pre-roll through tuning period to update RLS and sigma.
    idx = np.arange(len(d.index))
    tune_idx = idx[tune_mask]
    for t in tune_idx:
        if t - 1 < int(ar_order):
            continue
        # Update error EWMA from the last 1-step forecast (if available).
        if last_mu1 is not None:
            e = float(inflow[t] - float(last_mu1))
            err2_fast = infl_alpha * err2_fast + (1.0 - infl_alpha) * (e ** 2)

        if variant.rolling_calibration:
            # Observation used for update: potentially delayed/missing.
            obs_t = t - 1 - int(obs_delay_days)
            if obs_t >= int(ar_order):
                if float(obs_missing_rate) > 0.0 and float(rng.random()) < float(obs_missing_rate):
                    pass
                else:
                    phi = ar_feature_from_hist(inflow[: obs_t], order=int(ar_order))
                    rls = rls_update(
                        rls,
                        y_t=float(inflow[obs_t]),
                        phi_t=phi,
                        forgetting_factor=float(forgetting_factor),
                        sigma_ewma_alpha=float(sigma_ewma_alpha),
                    )

        # 1-step forecast for the next iteration's error update (predict day t+1 using history up to t).
        mu1 = ar_multistep_forecast_mean(
            inflow[: t + 1],
            theta=rls.theta if variant.rolling_calibration else theta_static,
            order=int(ar_order),
            horizon=1,
        )
        last_mu1 = float(max(0.0, mu1[0]))

    # Closed-loop simulation on the test set.
    test_idx = idx[test_mask]
    if test_idx.size == 0:
        raise ValueError("Empty test period after filtering.")

    # Start storage from observed storage at test start (state is measured).
    storage_obs = d["storage"].values.astype(float)
    s = float(storage_obs[int(test_idx[0])])
    storage_sim = [s]
    release_sim = []
    stage_cost = []
    violation = []
    inflow_real = []

    # Initialize previous release from observed outflow at day t-1 (or clamp to bounds).
    outflow_obs = d["outflow"].values.astype(float)
    t0 = int(test_idx[0])
    if t0 - 1 >= 0:
        r_prev = float(outflow_obs[t0 - 1])
    else:
        r_prev = float(np.mean(bounds_release_m3s))
    r_prev = float(np.clip(r_prev, bounds_release_m3s[0], bounds_release_m3s[1]))

    calib_s = 0.0
    dispatch_s = 0.0
    total_s = 0.0

    delta = float(m3s_to_mcm_per_day)
    loss = float(loss_mcm_per_day)

    for t in test_idx:
        t = int(t)
        t_start = time.perf_counter()

        # Update fast error EWMA based on yesterday's 1-step forecast.
        if last_mu1 is not None:
            e = float(inflow[t] - float(last_mu1))
            err2_fast = infl_alpha * err2_fast + (1.0 - infl_alpha) * (e ** 2)

        # Rolling calibration uses observation up to t-1.
        c0 = time.perf_counter()
        if variant.rolling_calibration:
            obs_t = t - 1 - int(obs_delay_days)
            if obs_t >= int(ar_order):
                if float(obs_missing_rate) > 0.0 and float(rng.random()) < float(obs_missing_rate):
                    pass
                else:
                    phi = ar_feature_from_hist(inflow[: obs_t], order=int(ar_order))
                    rls = rls_update(
                        rls,
                        y_t=float(inflow[obs_t]),
                        phi_t=phi,
                        forgetting_factor=float(forgetting_factor),
                        sigma_ewma_alpha=float(sigma_ewma_alpha),
                    )
        calib_s += time.perf_counter() - c0

        theta = rls.theta if variant.rolling_calibration else theta_static
        mu = ar_multistep_forecast_mean(inflow[:t], theta=theta, order=int(ar_order), horizon=int(horizon_days))
        mu = np.maximum(mu, 0.0)

        sigma = float(np.sqrt(float(rls.sigma2_ewma))) if variant.rolling_calibration else float(sigma_static)
        if variant.point_forecast_only:
            sigma = 0.0

        inflation = 1.0
        if variant.feedback_inflation and (sigma > 0.0):
            inflation = float(np.sqrt(float(err2_fast) / float(max(1e-12, rls.sigma2_ewma))))
            inflation = float(max(1.0, min(infl_max, inflation)))

        # Scenarios for dispatch.
        d0 = time.perf_counter()
        S = int(scenario_count) if variant.scenario_mpc else 1
        q_scen = np.zeros((S, int(horizon_days)), dtype=float)
        for s_idx in range(S):
            eps = rng.standard_normal(int(horizon_days)) if (sigma > 0.0 and S > 1) else np.zeros((int(horizon_days),))
            for h in range(int(horizon_days)):
                sigma_h = sigma * float(np.sqrt(h + 1))
                q_scen[s_idx, h] = max(0.0, float(mu[h]) + inflation * sigma_h * float(eps[h]))

        sol = solve_mpc_release_plan(
            s0_mcm=float(s),
            q_scenarios_m3s=q_scen,
            r_prev_m3s=float(r_prev),
            s_bounds_mcm=(float(bounds_storage_mcm[0]), float(bounds_storage_mcm[1])),
            r_bounds_m3s=(float(bounds_release_m3s[0]), float(bounds_release_m3s[1])),
            s_target_mcm=float(target_storage_mcm),
            m3s_to_mcm_per_day=float(delta),
            loss_mcm_per_day=float(loss),
            weights=dict(dispatch_weights),
            maxiter=80,
        )
        r_t = float(sol.release_plan[0])
        dispatch_s += time.perf_counter() - d0

        # Realize inflow for day t and advance storage.
        q_t = float(inflow[t])
        s_next = float(s + (q_t - r_t) * delta - loss)

        # Metrics.
        viol = (s_next < float(bounds_storage_mcm[0])) or (s_next > float(bounds_storage_mcm[1]))
        c = _stage_cost(
            s_next_mcm=s_next,
            r_m3s=r_t,
            r_prev_m3s=float(r_prev),
            bounds_mcm=(float(bounds_storage_mcm[0]), float(bounds_storage_mcm[1])),
            target_mcm=float(target_storage_mcm),
            weights=dict(dispatch_weights),
        )

        storage_sim.append(s_next)
        release_sim.append(r_t)
        inflow_real.append(q_t)
        stage_cost.append(c)
        violation.append(bool(viol))

        # Next step.
        s = s_next
        r_prev = r_t

        # 1-step forecast for next day's error update.
        mu1 = ar_multistep_forecast_mean(inflow[: t + 1], theta=theta, order=int(ar_order), horizon=1)
        last_mu1 = float(max(0.0, mu1[0]))

        total_s += time.perf_counter() - t_start

    import numpy as np

    viol_arr = np.asarray(violation, dtype=bool)
    stage_cost_arr = np.asarray(stage_cost, dtype=float)

    viol_rate = float(np.mean(viol_arr.astype(float))) if viol_arr.size else float("nan")
    reliability = float(1.0 - viol_rate) if np.isfinite(viol_rate) else float("nan")
    if np.any(viol_arr):
        s_next_arr = np.asarray(storage_sim[1:], dtype=float)
        mag = np.maximum(0.0, s_next_arr - float(bounds_storage_mcm[1])) + np.maximum(
            0.0, float(bounds_storage_mcm[0]) - s_next_arr
        )
        vuln = float(np.mean(mag[viol_arr])) / float(max(1e-9, (float(bounds_storage_mcm[1]) - float(bounds_storage_mcm[0]))))
    else:
        vuln = 0.0

    obj = float(np.mean(stage_cost_arr)) if stage_cost_arr.size else float("nan")

    timing = Timing(
        calib_s=float(calib_s / max(1, len(stage_cost_arr))),
        dispatch_s=float(dispatch_s / max(1, len(stage_cost_arr))),
        total_s=float(total_s / max(1, len(stage_cost_arr))),
    )

    return RolloutSummary(
        metrics={
            "violation_rate": viol_rate,
            "objective": obj,
            "reliability": reliability,
            "vulnerability": float(vuln),
        },
        timing=timing,
    )
