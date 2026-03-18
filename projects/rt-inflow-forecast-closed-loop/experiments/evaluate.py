#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from data.resopsus import load_resopsus_series
from forecast.ar import ar_multistep_forecast_mean, fit_ar_ridge, rls_init, rls_update, ar_feature_from_hist
from forecast.climatology import climatology_forecast_mean, fit_climatology
from forecast.lstm import LSTMConfig, lstm_multistep_forecast_mean, train_lstm
from metrics.metrics_stub import compute_metrics
from sim.closed_loop import estimate_bounds_and_loss
from sim.rollout import RolloutVariant, simulate_closed_loop_ar_mpc


def _experiments_dir() -> Path:
    return Path(__file__).resolve().parent


def _write_csv(path: Path, rows: List[Dict[str, Any]], *, header: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})


def _fmt_pm(mean: float, std: float, *, digits: int = 2) -> str:
    if not (np.isfinite(mean) and np.isfinite(std)):
        return "--"
    fmt = "{:." + str(int(digits)) + "f}"
    return fmt.format(float(mean)) + "$\\pm$" + fmt.format(float(std))


def _fmt_num(x: float, *, digits: int = 3) -> str:
    if not np.isfinite(x):
        return "--"
    fmt = "{:." + str(int(digits)) + "f}"
    return fmt.format(float(x))


def _write_tex_table(path: Path, *, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _date_splits(cfg: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    dcfg = cfg["data"]["resopsus"]
    start = str(dcfg["start_date"])
    end = str(dcfg["end_date"])
    train_end = str(dcfg["train_end"])
    tune_end = str(dcfg["tune_end"])
    test_end = str(dcfg["test_end"])
    return start, end, train_end, tune_end, test_end


def _forecast_eval_one_dam(
    *,
    series_df,
    cfg: Dict[str, Any],
    dam_seed: int,
    include_lstm: bool,
) -> Dict[str, Dict[str, float]]:
    """
    Returns per-method metrics for one dam.
    """
    import pandas as pd

    start, end, train_end, tune_end, test_end = _date_splits(cfg)
    horizon = int(cfg["evaluation"]["horizon_days"])
    metrics = list(cfg["evaluation"]["metrics"]["forecast"])
    ar_cfg = cfg["evaluation"]["rolling_calibration"]
    ar_order = int(ar_cfg["ar_order"])
    forgetting_factor = float(ar_cfg["forgetting_factor"])
    init_ridge = float(ar_cfg["init_ridge"])
    sigma_ewma_alpha = float(ar_cfg["sigma_ewma_alpha"])

    d = series_df.copy()
    d.index = pd.to_datetime(d.index)
    inflow = d["inflow"].values.astype(float)
    dates = d.index

    # Masks
    train_mask = dates <= pd.Timestamp(train_end)
    tune_mask = (dates > pd.Timestamp(train_end)) & (dates <= pd.Timestamp(tune_end))
    test_mask = (dates > pd.Timestamp(tune_end)) & (dates <= pd.Timestamp(test_end))
    idx = np.arange(len(dates))
    tune_idx = idx[tune_mask]
    test_idx = idx[test_mask]

    # Forecast models
    theta_static, _, sigma_static = fit_ar_ridge(inflow[train_mask], order=ar_order, ridge=1e-3)
    rls = rls_init(order=ar_order, init_ridge=init_ridge, theta0=theta_static, sigma0=sigma_static)

    # Warmup rolling calibration through tuning.
    last_mu1 = None
    for t in tune_idx:
        t = int(t)
        if t - 1 < ar_order:
            continue
        if last_mu1 is not None:
            # drive sigma update through rls_update below
            pass
        obs_t = t - 1
        if obs_t >= ar_order:
            phi = ar_feature_from_hist(inflow[:obs_t], order=ar_order)
            rls = rls_update(
                rls,
                y_t=float(inflow[obs_t]),
                phi_t=phi,
                forgetting_factor=forgetting_factor,
                sigma_ewma_alpha=sigma_ewma_alpha,
            )
        mu1 = ar_multistep_forecast_mean(inflow[: t + 1], theta=rls.theta, order=ar_order, horizon=1)
        last_mu1 = float(max(0.0, mu1[0]))

    # Climatology
    clim = fit_climatology(dates=dates[train_mask], y=inflow[train_mask])

    # LSTM (offline, per dam)
    lstm_art = None
    lstm_sigma = None
    if include_lstm:
        lcfg_raw = cfg["model"]["lstm"]
        lcfg = LSTMConfig(
            lookback_days=int(lcfg_raw["lookback_days"]),
            horizon_days=int(lcfg_raw["horizon_days"]),
            hidden_dim=int(lcfg_raw["hidden_dim"]),
            num_layers=int(lcfg_raw["num_layers"]),
            dropout=float(lcfg_raw["dropout"]),
        )
        tr_cfg = cfg["training"]
        device = str(cfg["project"].get("device", "cpu"))
        lstm_art = train_lstm(
            inflow_train=inflow[train_mask],
            inflow_tune=inflow[tune_mask],
            cfg=lcfg,
            seed=int(dam_seed),
            device=device,
            epochs=int(tr_cfg["epochs"]),
            batch_size=int(tr_cfg["batch_size"]),
            lr=float(tr_cfg["lr"]),
        )
        # Simple fixed sigma from tuning one-step errors.
        # (We keep uncertainty modeling lightweight and comparable.)
        errs = []
        for t in tune_idx:
            t = int(t)
            if t < lcfg.lookback_days:
                continue
            pred1 = lstm_multistep_forecast_mean(
                lstm_art, inflow_hist=inflow[:t], horizon=1, device=device
            )[0]
            errs.append(float(inflow[t] - pred1))
        lstm_sigma = float(np.std(np.asarray(errs, dtype=float), ddof=1)) if len(errs) > 10 else float(sigma_static)

    # Collect flattened forecasts (across horizons) for each method.
    methods = {
        "Persistence": {"mu": [], "sigma": []},
        "Climatology": {"mu": [], "sigma": []},
        "AR(p) static": {"mu": [], "sigma": []},
        "Rolling AR(p) (ours)": {"mu": [], "sigma": []},
    }
    if include_lstm:
        methods["ML-LSTM"] = {"mu": [], "sigma": []}

    targets = []

    # Fixed sigma for simple baselines.
    sigma_persist = float(np.std(np.diff(inflow[train_mask]), ddof=1)) if np.sum(train_mask) > 10 else float(sigma_static)
    sigma_clim = float(np.std(inflow[train_mask] - np.mean(inflow[train_mask]), ddof=1)) if np.sum(train_mask) > 10 else float(sigma_static)

    for t in test_idx:
        t = int(t)
        if t - 1 < ar_order:
            continue
        if t + horizon - 1 >= len(inflow):
            break

        # Rolling update with the most recent available observation (t-1) before forecasting day t.
        obs_t = t - 1
        phi = ar_feature_from_hist(inflow[:obs_t], order=ar_order)
        rls = rls_update(
            rls,
            y_t=float(inflow[obs_t]),
            phi_t=phi,
            forgetting_factor=forgetting_factor,
            sigma_ewma_alpha=sigma_ewma_alpha,
        )

        # Persistence uses last observed inflow (t-1).
        mu_p = np.full((horizon,), float(inflow[t - 1]), dtype=float)
        mu_c = climatology_forecast_mean(clim, start_date=dates[t], horizon=horizon)
        mu_a = ar_multistep_forecast_mean(inflow[:t], theta=theta_static, order=ar_order, horizon=horizon)
        mu_r = ar_multistep_forecast_mean(inflow[:t], theta=rls.theta, order=ar_order, horizon=horizon)

        mu_p = np.maximum(mu_p, 0.0)
        mu_c = np.maximum(mu_c, 0.0)
        mu_a = np.maximum(mu_a, 0.0)
        mu_r = np.maximum(mu_r, 0.0)

        # Per-horizon sigma scaling.
        sig_p = np.asarray([sigma_persist * np.sqrt(h + 1) for h in range(horizon)], dtype=float)
        sig_c = np.asarray([sigma_clim * np.sqrt(h + 1) for h in range(horizon)], dtype=float)
        sig_a = np.asarray([sigma_static * np.sqrt(h + 1) for h in range(horizon)], dtype=float)
        sig_r0 = float(np.sqrt(float(rls.sigma2_ewma)))
        sig_r = np.asarray([sig_r0 * np.sqrt(h + 1) for h in range(horizon)], dtype=float)

        if include_lstm and lstm_art is not None and lstm_sigma is not None:
            device = str(cfg["project"].get("device", "cpu"))
            mu_l = lstm_multistep_forecast_mean(lstm_art, inflow_hist=inflow[:t], horizon=horizon, device=device)
            mu_l = np.maximum(mu_l, 0.0)
            sig_l = np.asarray([float(lstm_sigma) * np.sqrt(h + 1) for h in range(horizon)], dtype=float)
        else:
            mu_l, sig_l = None, None

        y_true = inflow[t : t + horizon].astype(float)

        # Append flattened.
        targets.extend(y_true.tolist())
        methods["Persistence"]["mu"].extend(mu_p.tolist())
        methods["Persistence"]["sigma"].extend(sig_p.tolist())
        methods["Climatology"]["mu"].extend(mu_c.tolist())
        methods["Climatology"]["sigma"].extend(sig_c.tolist())
        methods["AR(p) static"]["mu"].extend(mu_a.tolist())
        methods["AR(p) static"]["sigma"].extend(sig_a.tolist())
        methods["Rolling AR(p) (ours)"]["mu"].extend(mu_r.tolist())
        methods["Rolling AR(p) (ours)"]["sigma"].extend(sig_r.tolist())
        if include_lstm and mu_l is not None:
            methods["ML-LSTM"]["mu"].extend(mu_l.tolist())
            methods["ML-LSTM"]["sigma"].extend(sig_l.tolist())

    targets_arr = np.asarray(targets, dtype=float)
    out: Dict[str, Dict[str, float]] = {}
    for name, ms in methods.items():
        mu = np.asarray(ms["mu"], dtype=float)
        sig = np.asarray(ms["sigma"], dtype=float)
        # Point metrics
        res = compute_metrics(predictions=mu, targets=targets_arr, metrics=[m for m in metrics if m in ("rmse", "mae", "nse")])
        # Probabilistic metrics
        prob = compute_metrics(predictions={"mu": mu, "sigma": sig}, targets=targets_arr, metrics=[m for m in metrics if m in ("crps", "coverage80")])
        res.update(prob)
        out[name] = res
    return out


def run_forecast_main(*, cfg: Dict[str, Any], results_dir: Path) -> None:
    out_csv = results_dir / "forecast_results.csv"
    out_tex = results_dir / "forecast_results_table.tex"
    out_json = results_dir / "forecast_results_per_dam.json"
    if out_csv.exists() and out_tex.exists():
        return

    dams = [int(x) for x in cfg["data"]["resopsus"]["dam_ids"]]
    per_dam: Dict[str, Dict[str, Dict[str, float]]] = {}

    for i, dam_id in enumerate(dams):
        series = load_resopsus_series(experiments_dir=_experiments_dir(), cfg=cfg, dam_id=dam_id)
        include_lstm = True
        per_dam[str(dam_id)] = _forecast_eval_one_dam(
            series_df=series.df,
            cfg=cfg,
            dam_seed=int(cfg["project"].get("seed", 42)) + i,
            include_lstm=include_lstm,
        )

    # Aggregate across dams: mean ± std. Use a fixed method order for stable tables.
    metrics = list(next(iter(next(iter(per_dam.values())).values())).keys())
    methods = [
        "Persistence",
        "Climatology",
        "AR(p) static",
        "ML-LSTM",
        "Rolling AR(p) (ours)",
    ]
    methods = [m for m in methods if m in next(iter(per_dam.values())).keys()]

    rows = []
    for m in methods:
        vals = {k: [] for k in metrics}
        for dam_id in per_dam:
            for k in metrics:
                vals[k].append(float(per_dam[dam_id][m][k]))
        row = {"method": m, "n_dams": len(per_dam)}
        for k in metrics:
            arr = np.asarray(vals[k], dtype=float)
            row[k + "_mean"] = float(np.mean(arr))
            row[k + "_std"] = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
        rows.append(row)

    header = ["method", "n_dams"] + [k + "_mean" for k in metrics] + [k + "_std" for k in metrics]
    _write_csv(out_csv, rows, header=header)
    out_json.write_text(json.dumps(per_dam, indent=2, sort_keys=True), encoding="utf-8")

    # LaTeX table body used by main.tex.
    def cell(r, key, digits=2):
        return _fmt_pm(float(r[key + "_mean"]), float(r[key + "_std"]), digits=digits)

    lines = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.34\\columnwidth}cccc}")
    lines.append("\\toprule")
    lines.append("Method & RMSE & NSE & CRPS & Cov. \\\\")
    lines.append("\\midrule")
    for r in rows:
        lines.append(
            "%s & %s & %s & %s & %s \\\\"
            % (
                r["method"],
                cell(r, "rmse", digits=2),
                cell(r, "nse", digits=3),
                cell(r, "crps", digits=2),
                cell(r, "coverage80", digits=3),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write_tex_table(out_tex, lines=lines)


def _ops_variants() -> List[RolloutVariant]:
    return [
        RolloutVariant(
            name="StaticCalib-OpenLoop-DetMPC",
            rolling_calibration=False,
            scenario_mpc=False,
            feedback_inflation=False,
        ),
        RolloutVariant(
            name="RollingCalib-OpenLoop-DetMPC",
            rolling_calibration=True,
            scenario_mpc=False,
            feedback_inflation=False,
        ),
        RolloutVariant(
            name="RollingCalib-OpenLoop-ScenarioMPC",
            rolling_calibration=True,
            scenario_mpc=True,
            feedback_inflation=False,
        ),
        RolloutVariant(
            name="RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)",
            rolling_calibration=True,
            scenario_mpc=True,
            feedback_inflation=True,
        ),
    ]


def _ablation_variants() -> List[RolloutVariant]:
    return [
        RolloutVariant(
            name="Full closed-loop method",
            rolling_calibration=True,
            scenario_mpc=True,
            feedback_inflation=True,
        ),
        RolloutVariant(
            name="w/o rolling calibration (static params)",
            rolling_calibration=False,
            scenario_mpc=True,
            feedback_inflation=True,
        ),
        RolloutVariant(
            name="w/o implementation feedback (open loop)",
            rolling_calibration=True,
            scenario_mpc=True,
            feedback_inflation=False,
        ),
        RolloutVariant(
            name="Deterministic dispatch (no scenarios)",
            rolling_calibration=True,
            scenario_mpc=False,
            feedback_inflation=False,
        ),
        RolloutVariant(
            name="Point forecast only (no UQ)",
            rolling_calibration=True,
            scenario_mpc=True,
            feedback_inflation=False,
            point_forecast_only=True,
        ),
    ]


def _run_ops_suite(
    *,
    cfg: Dict[str, Any],
    variants: List[RolloutVariant],
    results_csv: Path,
    results_tex: Path,
    title: str,
) -> None:
    if results_csv.exists() and results_tex.exists():
        return

    start, end, train_end, tune_end, test_end = _date_splits(cfg)
    dams = [int(x) for x in cfg["data"]["resopsus"]["dam_ids"]]

    dispatch_cfg = cfg["evaluation"]["dispatch"]
    m3s_to_mcm_per_day = float(dispatch_cfg["m3s_to_mcm_per_day"])
    s_q = tuple(dispatch_cfg["bounds"]["storage_quantiles"])
    r_q = tuple(dispatch_cfg["bounds"]["release_quantiles"])

    ar_cfg = cfg["evaluation"]["rolling_calibration"]
    horizon = int(cfg["evaluation"]["horizon_days"])
    scenario_count = int(cfg["evaluation"]["scenario_count"])
    seed = int(cfg["evaluation"].get("random_seed", cfg["project"].get("seed", 42)))

    weights = dict(dispatch_cfg["weights"])
    fb_cfg = dict(cfg["evaluation"]["feedback"])

    per_dam: Dict[str, Dict[str, Dict[str, float]]] = {}
    per_dam_timing: Dict[str, Dict[str, Dict[str, float]]] = {}

    for i, dam_id in enumerate(dams):
        series = load_resopsus_series(experiments_dir=_experiments_dir(), cfg=cfg, dam_id=dam_id)
        b = estimate_bounds_and_loss(
            df=series.df,
            train_end=train_end,
            m3s_to_mcm_per_day=m3s_to_mcm_per_day,
            storage_quantiles=(float(s_q[0]), float(s_q[1])),
            release_quantiles=(float(r_q[0]), float(r_q[1])),
        )

        per_dam[str(dam_id)] = {}
        per_dam_timing[str(dam_id)] = {}
        for v in variants:
            rng = np.random.default_rng(seed + 1000 * i + 17)
            res = simulate_closed_loop_ar_mpc(
                df=series.df,
                variant=v,
                ar_order=int(ar_cfg["ar_order"]),
                forgetting_factor=float(ar_cfg["forgetting_factor"]),
                init_ridge=float(ar_cfg["init_ridge"]),
                sigma_ewma_alpha=float(ar_cfg["sigma_ewma_alpha"]),
                horizon_days=horizon,
                scenario_count=scenario_count,
                m3s_to_mcm_per_day=m3s_to_mcm_per_day,
                bounds_storage_mcm=b.storage_mcm,
                bounds_release_m3s=b.release_m3s,
                target_storage_mcm=b.target_storage_mcm,
                loss_mcm_per_day=b.loss_mcm_per_day,
                dispatch_weights=weights,
                feedback_cfg=fb_cfg,
                train_end=train_end,
                tune_end=tune_end,
                test_end=test_end,
                rng=rng,
            )
            per_dam[str(dam_id)][v.name] = dict(res.metrics)
            per_dam_timing[str(dam_id)][v.name] = {
                "calib_s": float(res.timing.calib_s),
                "dispatch_s": float(res.timing.dispatch_s),
                "total_s": float(res.timing.total_s),
            }

    # Aggregate
    metric_keys = ["violation_rate", "objective", "reliability", "vulnerability"]
    rows = []
    for v in variants:
        row = {"method": v.name, "n_dams": len(dams)}
        for k in metric_keys:
            arr = np.asarray([per_dam[str(d)][v.name][k] for d in dams], dtype=float)
            row[k + "_mean"] = float(np.mean(arr))
            row[k + "_std"] = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
        rows.append(row)

    header = ["method", "n_dams"] + [k + "_mean" for k in metric_keys] + [k + "_std" for k in metric_keys]
    _write_csv(results_csv, rows, header=header)

    # LaTeX table body
    lines = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.34\\columnwidth}ccp{0.24\\columnwidth}}")
    lines.append("\\toprule")
    lines.append("Method & Viol. & Obj. ($\\times10^6$) & Notes \\\\")
    lines.append("\\midrule")
    for r in rows:
        viol = _fmt_pm(float(r["violation_rate_mean"]), float(r["violation_rate_std"]), digits=3)
        obj = _fmt_pm(float(r["objective_mean"]) / 1e6, float(r["objective_std"]) / 1e6, digits=2)
        note = title.get(r["method"], "") if isinstance(title, dict) else ""
        lines.append("%s & %s & %s & %s \\\\" % (r["method"].replace("_", "\\_"), viol, obj, note))
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write_tex_table(results_tex, lines=lines)

    # Save per-dam details for traceability.
    (results_csv.parent / (results_csv.stem + "_per_dam.json")).write_text(
        json.dumps(per_dam, indent=2, sort_keys=True), encoding="utf-8"
    )
    (results_csv.parent / (results_csv.stem + "_timing_per_dam.json")).write_text(
        json.dumps(per_dam_timing, indent=2, sort_keys=True), encoding="utf-8"
    )


def run_ops_main(*, cfg: Dict[str, Any], results_dir: Path) -> None:
    notes = {
        "StaticCalib-OpenLoop-DetMPC": "open-loop + static params",
        "RollingCalib-OpenLoop-DetMPC": "isolates rolling calibration",
        "RollingCalib-OpenLoop-ScenarioMPC": "isolates uncertainty-aware dispatch",
        "RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)": "closed-loop coupling",
    }
    _run_ops_suite(
        cfg=cfg,
        variants=_ops_variants(),
        results_csv=results_dir / "main_results.csv",
        results_tex=results_dir / "main_results_table.tex",
        title=notes,
    )


def run_ops_ablation(*, cfg: Dict[str, Any], results_dir: Path) -> None:
    notes = {
        "Full closed-loop method": "reference",
        "w/o rolling calibration (static params)": "ablate COMP-2",
        "w/o implementation feedback (open loop)": "ablate COMP-6",
        "Deterministic dispatch (no scenarios)": "ablate uncertainty propagation",
        "Point forecast only (no UQ)": "remove probabilistic forecasts",
    }
    _run_ops_suite(
        cfg=cfg,
        variants=_ablation_variants(),
        results_csv=results_dir / "ablation_results.csv",
        results_tex=results_dir / "ablation_results_table.tex",
        title=notes,
    )


def run_robustness(*, cfg: Dict[str, Any], results_dir: Path) -> None:
    out_csv = results_dir / "robustness_results.csv"
    out_tex = results_dir / "robustness_table.tex"
    if out_csv.exists() and out_tex.exists():
        return

    start, end, train_end, tune_end, test_end = _date_splits(cfg)
    dams = [int(x) for x in cfg["data"]["resopsus"]["dam_ids"]]

    dispatch_cfg = cfg["evaluation"]["dispatch"]
    m3s_to_mcm_per_day = float(dispatch_cfg["m3s_to_mcm_per_day"])
    s_q = tuple(dispatch_cfg["bounds"]["storage_quantiles"])
    r_q = tuple(dispatch_cfg["bounds"]["release_quantiles"])
    weights = dict(dispatch_cfg["weights"])
    fb_cfg = dict(cfg["evaluation"]["feedback"])

    ar_cfg = cfg["evaluation"]["rolling_calibration"]
    horizon = int(cfg["evaluation"]["horizon_days"])
    scenario_count = int(cfg["evaluation"]["scenario_count"])
    seed = int(cfg["evaluation"].get("random_seed", cfg["project"].get("seed", 42)))

    # Stress 1: multiplicative inflow regime shift.
    alphas = [0.8, 0.9, 1.0, 1.1, 1.2]
    methods = [
        RolloutVariant("StaticCalib-OpenLoop-DetMPC", False, False, False),
        RolloutVariant("RollingCalib-OpenLoop-DetMPC", True, False, False),
        RolloutVariant("RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)", True, True, True),
    ]

    rows = []
    for a in alphas:
        for v in methods:
            vals = {k: [] for k in ("violation_rate", "objective")}
            for i, dam_id in enumerate(dams):
                series = load_resopsus_series(experiments_dir=_experiments_dir(), cfg=cfg, dam_id=dam_id)
                b = estimate_bounds_and_loss(
                    df=series.df,
                    train_end=train_end,
                    m3s_to_mcm_per_day=m3s_to_mcm_per_day,
                    storage_quantiles=(float(s_q[0]), float(s_q[1])),
                    release_quantiles=(float(r_q[0]), float(r_q[1])),
                )
                rng = np.random.default_rng(seed + 1000 * i + int(a * 100))
                res = simulate_closed_loop_ar_mpc(
                    df=series.df,
                    variant=v,
                    ar_order=int(ar_cfg["ar_order"]),
                    forgetting_factor=float(ar_cfg["forgetting_factor"]),
                    init_ridge=float(ar_cfg["init_ridge"]),
                    sigma_ewma_alpha=float(ar_cfg["sigma_ewma_alpha"]),
                    horizon_days=horizon,
                    scenario_count=scenario_count,
                    m3s_to_mcm_per_day=m3s_to_mcm_per_day,
                    bounds_storage_mcm=b.storage_mcm,
                    bounds_release_m3s=b.release_m3s,
                    target_storage_mcm=b.target_storage_mcm,
                    loss_mcm_per_day=b.loss_mcm_per_day,
                    dispatch_weights=weights,
                    feedback_cfg=fb_cfg,
                    train_end=train_end,
                    tune_end=tune_end,
                    test_end=test_end,
                    rng=rng,
                    inflow_scale_alpha=float(a),
                )
                vals["violation_rate"].append(float(res.metrics["violation_rate"]))
                vals["objective"].append(float(res.metrics["objective"]))
            rows.append(
                {
                    "stress": "inflow_scale",
                    "severity": a,
                    "method": v.name,
                    "violation_rate_mean": float(np.mean(vals["violation_rate"])),
                    "objective_mean": float(np.mean(vals["objective"])),
                }
            )

    # Stress 2: sparse/delayed observations (rolling method only).
    miss_rates = [0.0, 0.1, 0.3, 0.5]
    delays = [0, 1, 3]
    v = RolloutVariant("Closed-loop (ours)", True, True, True)
    for mr in miss_rates:
        for dly in delays:
            vals = {k: [] for k in ("violation_rate", "objective")}
            for i, dam_id in enumerate(dams):
                series = load_resopsus_series(experiments_dir=_experiments_dir(), cfg=cfg, dam_id=dam_id)
                b = estimate_bounds_and_loss(
                    df=series.df,
                    train_end=train_end,
                    m3s_to_mcm_per_day=m3s_to_mcm_per_day,
                    storage_quantiles=(float(s_q[0]), float(s_q[1])),
                    release_quantiles=(float(r_q[0]), float(r_q[1])),
                )
                rng = np.random.default_rng(seed + 2000 * i + int(mr * 1000) + 97 * int(dly))
                res = simulate_closed_loop_ar_mpc(
                    df=series.df,
                    variant=v,
                    ar_order=int(ar_cfg["ar_order"]),
                    forgetting_factor=float(ar_cfg["forgetting_factor"]),
                    init_ridge=float(ar_cfg["init_ridge"]),
                    sigma_ewma_alpha=float(ar_cfg["sigma_ewma_alpha"]),
                    horizon_days=horizon,
                    scenario_count=scenario_count,
                    m3s_to_mcm_per_day=m3s_to_mcm_per_day,
                    bounds_storage_mcm=b.storage_mcm,
                    bounds_release_m3s=b.release_m3s,
                    target_storage_mcm=b.target_storage_mcm,
                    loss_mcm_per_day=b.loss_mcm_per_day,
                    dispatch_weights=weights,
                    feedback_cfg=fb_cfg,
                    train_end=train_end,
                    tune_end=tune_end,
                    test_end=test_end,
                    rng=rng,
                    obs_missing_rate=float(mr),
                    obs_delay_days=int(dly),
                )
                vals["violation_rate"].append(float(res.metrics["violation_rate"]))
                vals["objective"].append(float(res.metrics["objective"]))
            rows.append(
                {
                    "stress": "obs_sparse_delay",
                    "severity": "miss=%.1f,delay=%d" % (float(mr), int(dly)),
                    "method": v.name,
                    "violation_rate_mean": float(np.mean(vals["violation_rate"])),
                    "objective_mean": float(np.mean(vals["objective"])),
                }
            )

    header = ["stress", "severity", "method", "violation_rate_mean", "objective_mean"]
    _write_csv(out_csv, rows, header=header)

    # Simple LaTeX table (compact).
    lines = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.26\\columnwidth}p{0.22\\columnwidth}p{0.30\\columnwidth}cc}")
    lines.append("\\toprule")
    lines.append("Stress & Severity & Method & Viol. & Obj. ($\\times10^6$) \\\\")
    lines.append("\\midrule")
    for r in rows[: min(18, len(rows))]:
        lines.append(
            "%s & %s & %s & %s & %s \\\\"
            % (
                str(r["stress"]).replace("_", "\\_"),
                str(r["severity"]),
                r["method"].replace("_", "\\_"),
                _fmt_num(float(r["violation_rate_mean"]), digits=3),
                _fmt_num(float(r["objective_mean"]) / 1e6, digits=2),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write_tex_table(out_tex, lines=lines)


def run_efficiency(*, cfg: Dict[str, Any], results_dir: Path) -> None:
    out_csv = results_dir / "efficiency_results.csv"
    out_tex = results_dir / "efficiency_table.tex"
    if out_csv.exists() and out_tex.exists():
        return

    # Efficiency is based on timing recorded during the ops suite.
    timing_json = results_dir / "main_results_timing_per_dam.json"
    if not timing_json.exists():
        run_ops_main(cfg=cfg, results_dir=results_dir)
    timing = json.loads(timing_json.read_text(encoding="utf-8"))

    methods = [
        "StaticCalib-OpenLoop-DetMPC",
        "RollingCalib-OpenLoop-ScenarioMPC",
        "RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)",
    ]
    dams = sorted(timing.keys())
    rows = []
    for m in methods:
        calib = []
        disp = []
        tot = []
        for d in dams:
            calib.append(float(timing[d][m]["calib_s"]))
            disp.append(float(timing[d][m]["dispatch_s"]))
            tot.append(float(timing[d][m]["total_s"]))
        rows.append(
            {
                "method": m,
                "calib_s_mean": float(np.mean(calib)),
                "dispatch_s_mean": float(np.mean(disp)),
                "total_s_mean": float(np.mean(tot)),
            }
        )

    header = ["method", "calib_s_mean", "dispatch_s_mean", "total_s_mean"]
    _write_csv(out_csv, rows, header=header)

    lines = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.44\\columnwidth}ccc}")
    lines.append("\\toprule")
    lines.append("Method & Calib (s) & Dispatch (s) & Total (s) \\\\")
    lines.append("\\midrule")
    for r in rows:
        lines.append(
            "%s & %s & %s & %s \\\\"
            % (
                r["method"].replace("_", "\\_"),
                _fmt_num(float(r["calib_s_mean"]), digits=3),
                _fmt_num(float(r["dispatch_s_mean"]), digits=3),
                _fmt_num(float(r["total_s_mean"]), digits=3),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write_tex_table(out_tex, lines=lines)


def run_experiment(*, row: Any, cfg: Dict[str, Any], results_dir: Path) -> None:
    """
    Dispatch to the right experiment suite based on the experiment matrix row.

    We intentionally compute results at the suite level (not per-row) to avoid
    redundant reruns. Each suite is idempotent and writes deterministic outputs.
    """
    # Forecast suite is triggered by any forecast main_comparison row.
    if str(row.type).strip() == "main_comparison" and str(row.experiment_id).startswith("EXP-FCST"):
        run_forecast_main(cfg=cfg, results_dir=results_dir)
        return

    # Operational main suite is triggered by any ops main_comparison row.
    if str(row.type).strip() == "main_comparison" and str(row.experiment_id).startswith("EXP-OP"):
        run_ops_main(cfg=cfg, results_dir=results_dir)
        return

    if str(row.type).strip() == "ablation":
        run_ops_ablation(cfg=cfg, results_dir=results_dir)
        return

    if str(row.type).strip() == "robustness":
        run_robustness(cfg=cfg, results_dir=results_dir)
        return

    if str(row.type).strip() == "efficiency":
        run_efficiency(cfg=cfg, results_dir=results_dir)
        return

    # Unknown/optional row types: no-op.
    return
