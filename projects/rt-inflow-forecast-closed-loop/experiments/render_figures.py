#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def _experiments_dir() -> Path:
    return Path(__file__).resolve().parent


def _paper_dir() -> Path:
    return (_experiments_dir().parent / "paper").resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _okabe_ito() -> Dict[str, str]:
    # Colorblind-friendly palette (Okabe-Ito).
    return {
        "black": "#000000",
        "orange": "#E69F00",
        "sky": "#56B4E9",
        "green": "#009E73",
        "yellow": "#F0E442",
        "blue": "#0072B2",
        "vermillion": "#D55E00",
        "purple": "#CC79A7",
        "gray": "#7F7F7F",
    }


def _mpl_setup() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 9,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class DamLabel:
    dam_id: int
    short: str
    long: str


def _dam_labels(cfg: Dict[str, Any]) -> list[DamLabel]:
    from data.resopsus import load_resopsus_series

    dams = [int(x) for x in cfg["data"]["resopsus"]["dam_ids"]]
    labels: list[DamLabel] = []
    for dam_id in dams:
        series = load_resopsus_series(experiments_dir=_experiments_dir(), cfg=cfg, dam_id=dam_id)
        short = f"{series.dam_name} ({series.state})"
        long = f"{series.dam_name} (DAM_ID {dam_id}, {series.state})"
        labels.append(DamLabel(dam_id=dam_id, short=short, long=long))
    return labels


def _short_method_label(method: str) -> str:
    # Standardize labels across plots (avoid legend/tick overflow).
    m = str(method)
    mapping = {
        # Ops pipelines.
        "StaticCalib-OpenLoop-DetMPC": "Static det. MPC (baseline)",
        "RollingCalib-OpenLoop-DetMPC": "Rolling det. MPC",
        "RollingCalib-OpenLoop-ScenarioMPC": "Rolling scenario MPC",
        "RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)": "Closed-loop scenario MPC (ours)",
        # Robustness obs suite.
        "Closed-loop (ours)": "Closed-loop (ours)",
    }
    if m in mapping:
        return mapping[m]
    return m


def plot_inflow_timeseries_splits(*, cfg: Dict[str, Any], outpath: Path) -> None:
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    from data.resopsus import load_resopsus_series

    colors = _okabe_ito()

    train_end = pd.to_datetime(cfg["data"]["resopsus"]["train_end"])
    tune_end = pd.to_datetime(cfg["data"]["resopsus"]["tune_end"])
    start = pd.to_datetime(cfg["data"]["resopsus"]["start_date"])
    end = pd.to_datetime(cfg["data"]["resopsus"]["end_date"])

    labels = _dam_labels(cfg)
    fig, axes = plt.subplots(nrows=len(labels), ncols=1, figsize=(7.2, 4.9), sharex=True)
    if len(labels) == 1:
        axes = [axes]

    for ax, lab in zip(axes, labels):
        series = load_resopsus_series(experiments_dir=_experiments_dir(), cfg=cfg, dam_id=int(lab.dam_id))
        df = series.df

        # Background shading for splits.
        ax.axvspan(start, train_end, color="#F2F2F2", zorder=0)
        ax.axvspan(train_end, tune_end, color="#FFF2CC", zorder=0)
        ax.axvspan(tune_end, end, color="#DDEBF7", zorder=0)
        ax.axvline(train_end, color="0.3", lw=0.7, ls="--")
        ax.axvline(tune_end, color="0.3", lw=0.7, ls="--")

        ax.plot(df.index, df["inflow"].values, lw=0.25, color=colors["blue"], alpha=0.9)
        ax.set_title(lab.long, loc="left")
        ax.set_ylabel("Inflow\n(m$^3$/s)")
        ax.grid(True, axis="y", alpha=0.25)

    axes[-1].set_xlabel("Date")

    legend_handles = [
        Patch(facecolor="#F2F2F2", edgecolor="none", label="Train (1980--2010)"),
        Patch(facecolor="#FFF2CC", edgecolor="none", label="Tune (2011--2014)"),
        Patch(facecolor="#DDEBF7", edgecolor="none", label="Test (2015--2020)"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.03))
    # Reserve top margin for the figure-level legend.
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def _bar_offsets(n: int) -> list[float]:
    if n <= 0:
        return []
    w = 0.8 / n
    x0 = -(0.8 - w) / 2.0
    return [x0 + i * w for i in range(n)]


def plot_forecast_skill_by_dam(*, cfg: Dict[str, Any], results_dir: Path, outpath: Path) -> None:
    import numpy as np
    import matplotlib.pyplot as plt

    colors = _okabe_ito()

    per_dam = _load_json(results_dir / "forecast_results_per_dam.json")
    labs = _dam_labels(cfg)

    methods = [
        ("AR(p) static", colors["black"]),
        ("ML-LSTM", colors["orange"]),
        ("Rolling AR(p) (ours)", colors["blue"]),
    ]

    x = np.arange(len(labs), dtype=float)
    offs = _bar_offsets(len(methods))
    width = 0.8 / len(methods)

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(4.4, 3.2), sharex=True)
    ax1, ax2 = axes[0], axes[1]

    for (name, c), dx in zip(methods, offs):
        crps = [float(per_dam[str(l.dam_id)][name]["crps"]) for l in labs]
        rmse = [float(per_dam[str(l.dam_id)][name]["rmse"]) for l in labs]
        ax1.bar(x + dx, crps, width=width, label=name, color=c, alpha=0.9)
        ax2.bar(x + dx, rmse, width=width, label=name, color=c, alpha=0.9)

    ax1.set_ylabel("CRPS (lower is better)")
    ax1.set_title("Forecast skill by reservoir (test 2015--2020; $H$=7 days)", loc="left")
    ax1.grid(True, axis="y", alpha=0.25)

    ax2.set_ylabel("RMSE")
    ax2.grid(True, axis="y", alpha=0.25)
    ax2.set_xticks(x)
    ax2.set_xticklabels([l.short for l in labs])

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_forecast_calibration_tradeoff(*, cfg: Dict[str, Any], results_dir: Path, outpath: Path) -> None:
    """
    Visualize the calibration/sharpness tradeoff using summary metrics:
    coverage of the nominal 80% interval vs CRPS change (relative to the static AR baseline).
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    colors = _okabe_ito()

    per_dam = _load_json(results_dir / "forecast_results_per_dam.json")
    labs = _dam_labels(cfg)

    methods = [
        ("AR(p) static", colors["black"]),
        ("ML-LSTM", colors["orange"]),
        ("Rolling AR(p) (ours)", colors["blue"]),
        ("Persistence", colors["gray"]),
    ]

    baseline = "AR(p) static"
    dam_markers = ["o", "s", "D", "^", "v", "P", "X"]
    dam_to_marker = {lab.dam_id: dam_markers[i % len(dam_markers)] for i, lab in enumerate(labs)}

    fig, ax = plt.subplots(figsize=(4.4, 2.6))

    cov_vals = []
    crps_pct_vals = []
    for lab in labs:
        dam = str(lab.dam_id)
        if dam not in per_dam or baseline not in per_dam[dam]:
            continue
        base_crps = float(per_dam[dam][baseline]["crps"])
        for name, c in methods:
            if name not in per_dam[dam]:
                continue
            cov = float(per_dam[dam][name]["coverage80"])
            crps = float(per_dam[dam][name]["crps"])
            crps_pct = 100.0 * (crps - base_crps) / max(1e-12, base_crps)
            cov_vals.append(cov)
            crps_pct_vals.append(crps_pct)
            ax.scatter(
                cov,
                crps_pct,
                s=30,
                marker=dam_to_marker.get(lab.dam_id, "o"),
                color=c,
                edgecolor="white",
                linewidth=0.4,
                zorder=3,
            )

    ax.axvline(0.8, color="0.3", lw=0.8, ls="--")
    ax.axhline(0.0, color="0.2", lw=0.8)
    ax.set_xlabel("80% interval coverage")
    ax.set_ylabel("CRPS change (%) vs static AR baseline\n(negative is better)")
    ax.set_title("Calibration vs sharpness (test 2015--2020; $H$=7 days)", loc="left")
    ax.grid(True, axis="both", alpha=0.25)

    if cov_vals:
        x0 = float(min(cov_vals))
        x1 = float(max(cov_vals))
        pad = 0.02
        ax.set_xlim(max(0.0, x0 - pad), min(1.0, x1 + pad))
    if crps_pct_vals:
        y0 = float(min(crps_pct_vals))
        y1 = float(max(crps_pct_vals))
        pad = 0.12 * max(1e-6, (y1 - y0))
        ax.set_ylim(y0 - pad, y1 + pad)

    method_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor="white", markersize=6, label=n)
        for n, c in methods
    ]
    dam_handles = [
        Line2D([0], [0], marker=dam_to_marker[lab.dam_id], color="none", markerfacecolor="0.85", markeredgecolor="0.2", markersize=6, label=lab.short)
        for lab in labs
    ]
    leg1 = ax.legend(handles=method_handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.30))
    ax.add_artist(leg1)
    ax.legend(handles=dam_handles, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.18))

    fig.tight_layout(rect=(0, 0, 1, 0.92))

    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_ops_by_dam(*, cfg: Dict[str, Any], results_dir: Path, outpath: Path) -> None:
    import numpy as np
    import matplotlib.pyplot as plt

    colors = _okabe_ito()

    per_dam = _load_json(results_dir / "main_results_per_dam.json")
    labs = _dam_labels(cfg)

    baseline = "StaticCalib-OpenLoop-DetMPC"
    methods = [
        ("StaticCalib-OpenLoop-DetMPC", colors["gray"]),
        ("RollingCalib-OpenLoop-DetMPC", colors["black"]),
        ("RollingCalib-OpenLoop-ScenarioMPC", colors["orange"]),
        ("RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)", colors["blue"]),
    ]

    x = np.arange(len(labs), dtype=float)
    offs = _bar_offsets(len(methods))
    width = 0.8 / len(methods)

    def obj_pct(dam_id: int, method: str) -> float:
        b = float(per_dam[str(dam_id)][baseline]["objective"])
        o = float(per_dam[str(dam_id)][method]["objective"])
        return 100.0 * (o - b) / max(1e-12, b)

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(4.4, 3.3), sharex=True)
    ax1, ax2 = axes[0], axes[1]

    for (name, c), dx in zip(methods, offs):
        vals = [obj_pct(l.dam_id, name) for l in labs]
        ax1.bar(x + dx, vals, width=width, label=_short_method_label(name), color=c, alpha=0.9)

    ax1.axhline(0.0, color="0.2", lw=0.8)
    ax1.set_ylabel("Objective change (%)\nvs static baseline\n(negative is better)")
    ax1.set_title("Operational value by reservoir (test 2015--2020)", loc="left")
    ax1.grid(True, axis="y", alpha=0.25)

    for (name, c), dx in zip(methods, offs):
        viol = [float(per_dam[str(l.dam_id)][name]["violation_rate"]) for l in labs]
        ax2.bar(x + dx, viol, width=width, label=_short_method_label(name), color=c, alpha=0.9)

    ax2.set_ylabel("Violation rate")
    ax2.grid(True, axis="y", alpha=0.25)
    ax2.set_xticks(x)
    ax2.set_xticklabels([l.short for l in labs])

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.90))

    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_runtime_value_tradeoff(*, cfg: Dict[str, Any], results_dir: Path, outpath: Path) -> None:
    """
    Plot the tradeoff between compute cost (runtime) and operational value (objective change).

    Uses per-dam timing to compute mean±std runtime (ms) per cycle, and per-dam objective
    to compute mean±std objective change (%) relative to the static deterministic baseline.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    colors = _okabe_ito()

    per_dam_obj = _load_json(results_dir / "main_results_per_dam.json")
    per_dam_time = _load_json(results_dir / "main_results_timing_per_dam.json")
    labs = _dam_labels(cfg)
    dams = [str(l.dam_id) for l in labs]

    baseline = "StaticCalib-OpenLoop-DetMPC"
    methods = [
        ("StaticCalib-OpenLoop-DetMPC", colors["gray"], "o"),
        ("RollingCalib-OpenLoop-DetMPC", colors["black"], "s"),
        ("RollingCalib-OpenLoop-ScenarioMPC", colors["orange"], "D"),
        ("RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)", colors["blue"], "^"),
    ]

    pts = {}
    for name, c, mk in methods:
        xs = []
        ys = []
        for dam in dams:
            if dam not in per_dam_obj or dam not in per_dam_time:
                continue
            if name not in per_dam_obj[dam] or baseline not in per_dam_obj[dam]:
                continue
            if name not in per_dam_time[dam]:
                continue
            t_ms = 1000.0 * float(per_dam_time[dam][name]["total_s"])
            b = float(per_dam_obj[dam][baseline]["objective"])
            o = float(per_dam_obj[dam][name]["objective"])
            obj_pct = 100.0 * (o - b) / max(1e-12, b)
            xs.append(t_ms)
            ys.append(obj_pct)
        if not xs:
            continue
        pts[name] = {
            "x_mean": float(np.mean(xs)),
            "x_std": float(np.std(xs, ddof=1)) if len(xs) > 1 else 0.0,
            "y_mean": float(np.mean(ys)),
            "y_std": float(np.std(ys, ddof=1)) if len(ys) > 1 else 0.0,
            "color": c,
            "marker": mk,
        }

    fig, ax = plt.subplots(figsize=(4.4, 2.8))
    ax.axhline(0.0, color="0.2", lw=0.8)

    # Draw points with error bars and in-plot labels.
    for name, _, _ in methods:
        if name not in pts:
            continue
        p = pts[name]
        ax.errorbar(
            p["x_mean"],
            p["y_mean"],
            xerr=p["x_std"],
            yerr=p["y_std"],
            fmt=p["marker"],
            ms=5.5,
            color=p["color"],
            ecolor="0.35",
            elinewidth=0.9,
            capsize=2,
            zorder=3,
        )
        ax.annotate(
            _short_method_label(name),
            (p["x_mean"], p["y_mean"]),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=7,
        )

    # Guide arrows showing the pipeline progression.
    chain = [
        "StaticCalib-OpenLoop-DetMPC",
        "RollingCalib-OpenLoop-DetMPC",
        "RollingCalib-OpenLoop-ScenarioMPC",
        "RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)",
    ]
    for a, b in zip(chain[:-1], chain[1:]):
        if a in pts and b in pts:
            ax.annotate(
                "",
                xy=(pts[b]["x_mean"], pts[b]["y_mean"]),
                xytext=(pts[a]["x_mean"], pts[a]["y_mean"]),
                arrowprops=dict(arrowstyle="->", lw=0.9, color="0.45"),
                zorder=2,
            )

    ax.set_xlabel("Runtime per cycle (ms)")
    ax.set_ylabel("Objective change (%) vs static baseline\n(negative is better)")
    ax.set_title("Compute--value tradeoff (mean$\\pm$std over reservoirs)", loc="left")
    ax.grid(True, axis="both", alpha=0.25)

    fig.tight_layout()
    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_runtime_value_tradeoff_v2(*, cfg: Dict[str, Any], results_dir: Path, outpath: Path) -> None:
    """
    Plot the compute/value tradeoff directly at the reservoir level.

    This avoids summarizing only three reservoirs into mean+-std error bars, which
    visually overlap and are easy to over-interpret as statistical uncertainty.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    colors = _okabe_ito()

    per_dam_obj = _load_json(results_dir / "main_results_per_dam.json")
    per_dam_time = _load_json(results_dir / "main_results_timing_per_dam.json")
    labs = _dam_labels(cfg)
    dams = [str(l.dam_id) for l in labs]

    baseline = "StaticCalib-OpenLoop-DetMPC"
    methods = [
        ("StaticCalib-OpenLoop-DetMPC", colors["gray"]),
        ("RollingCalib-OpenLoop-DetMPC", colors["black"]),
        ("RollingCalib-OpenLoop-ScenarioMPC", colors["orange"]),
        ("RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)", colors["blue"]),
    ]
    dam_markers = ["o", "s", "D", "^", "v", "P", "X"]
    dam_to_marker = {str(l.dam_id): dam_markers[i % len(dam_markers)] for i, l in enumerate(labs)}

    chains = {}
    x_vals = []
    y_vals = []
    for dam in dams:
        if dam not in per_dam_obj or dam not in per_dam_time:
            continue
        chain = []
        for name, color in methods:
            if name not in per_dam_obj[dam] or baseline not in per_dam_obj[dam]:
                continue
            if name not in per_dam_time[dam]:
                continue
            t_ms = 1000.0 * float(per_dam_time[dam][name]["total_s"])
            b = float(per_dam_obj[dam][baseline]["objective"])
            o = float(per_dam_obj[dam][name]["objective"])
            obj_pct = 100.0 * (o - b) / max(1e-12, b)
            chain.append((name, t_ms, obj_pct, color))
            x_vals.append(t_ms)
            y_vals.append(obj_pct)
        if chain:
            chains[dam] = chain

    fig, ax = plt.subplots(figsize=(4.4, 3.0))
    ax.axhline(0.0, color="0.2", lw=0.8)

    for dam in dams:
        if dam not in chains:
            continue
        xs = [pt[1] for pt in chains[dam]]
        ys = [pt[2] for pt in chains[dam]]
        ax.plot(xs, ys, color="0.72", lw=0.9, alpha=0.9, zorder=1)

    for dam in dams:
        if dam not in chains:
            continue
        marker = dam_to_marker.get(dam, "o")
        for _, x_ms, y_pct, color in chains[dam]:
            ax.scatter(
                x_ms,
                y_pct,
                s=36,
                marker=marker,
                color=color,
                edgecolor="white",
                linewidth=0.4,
                zorder=3,
            )

    ax.set_xscale("log")
    ax.set_xlabel("Runtime per cycle (ms, log scale)")
    ax.set_ylabel("Objective change (%) vs static baseline\n(negative is better)")
    ax.set_title("Compute--value tradeoff by reservoir", loc="left")
    ax.grid(True, axis="both", alpha=0.25)

    if x_vals:
        ax.set_xlim(0.8 * min(x_vals), 1.25 * max(x_vals))
    if y_vals:
        y_lo = min(y_vals)
        y_hi = max(y_vals)
        pad = 0.12 * max(1e-6, (y_hi - y_lo))
        ax.set_ylim(y_lo - pad, y_hi + pad)

    method_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor="white", markersize=6, label=_short_method_label(name))
        for name, color in methods
    ]
    dam_handles = [
        Line2D([0], [0], marker=dam_to_marker[str(l.dam_id)], color="none", markerfacecolor="0.85", markeredgecolor="0.2", markersize=6, label=l.short)
        for l in labs
    ]
    leg1 = ax.legend(handles=method_handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.31))
    ax.add_artist(leg1)
    ax.legend(handles=dam_handles, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.18))

    fig.tight_layout(rect=(0, 0, 1, 0.91))
    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_robustness_inflow_scale(*, results_dir: Path, outpath: Path) -> None:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    colors = _okabe_ito()

    df = pd.read_csv(results_dir / "robustness_results.csv")
    d = df[df["stress"] == "inflow_scale"].copy()
    d["alpha"] = d["severity"].astype(float)
    d = d.sort_values(["method", "alpha"])

    baseline = "StaticCalib-OpenLoop-DetMPC"
    methods = [
        ("StaticCalib-OpenLoop-DetMPC", colors["gray"]),
        ("RollingCalib-OpenLoop-DetMPC", colors["black"]),
        ("RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)", colors["blue"]),
    ]

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(4.4, 3.1), sharex=True)
    ax1, ax2 = axes[0], axes[1]

    base = d[d["method"] == baseline].copy()
    if base.empty:
        raise ValueError(f"Missing baseline rows for method='{baseline}' in robustness_results.csv.")
    base = base.sort_values("alpha").set_index("alpha")

    all_obj = []
    all_viol = []
    for name, c in methods:
        dd = d[d["method"] == name].copy()
        dd = dd.sort_values("alpha").set_index("alpha")
        common = dd.index.intersection(base.index)
        if common.empty:
            continue
        dd = dd.loc[common]
        bb = base.loc[common]

        # Objective is a cost: negative change is better.
        obj_pct = 100.0 * (dd["objective_mean"].astype(float) - bb["objective_mean"].astype(float)) / bb[
            "objective_mean"
        ].astype(float).clip(lower=1e-12)
        # Violation-rate change in percentage points.
        viol_pp = 100.0 * (dd["violation_rate_mean"].astype(float) - bb["violation_rate_mean"].astype(float))

        all_obj.append(obj_pct.to_numpy())
        all_viol.append(viol_pp.to_numpy())

        ax1.plot(
            common.to_numpy(),
            obj_pct.to_numpy(),
            marker="o",
            ms=3,
            lw=1.2,
            color=c,
            label=_short_method_label(name),
        )
        ax2.plot(
            common.to_numpy(),
            viol_pp.to_numpy(),
            marker="o",
            ms=3,
            lw=1.2,
            color=c,
            label=_short_method_label(name),
        )

    ax1.axhline(0.0, color="0.2", lw=0.8)
    ax2.axhline(0.0, color="0.2", lw=0.8)

    ax1.set_ylabel("Objective change (%)\nvs static baseline\n(negative is better)")
    ax1.set_title("Robustness: synthetic inflow scaling", loc="left")
    ax1.grid(True, axis="y", alpha=0.25)

    if all_obj:
        max_abs = float(np.nanmax(np.abs(np.concatenate(all_obj))))
        if max_abs > 0:
            ax1.set_ylim(-1.05 * max_abs, 1.05 * max_abs)

    ax2.set_ylabel("Violation change (pp)\nvs static baseline")
    ax2.set_xlabel("Inflow scaling $\\alpha$")
    ax2.grid(True, axis="y", alpha=0.25)

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.90))

    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def _parse_obs_severity(s: str) -> Tuple[float, int]:
    # Format: "miss=0.3,delay=1"
    s = str(s).strip().replace("\"", "")
    parts = [p.strip() for p in s.split(",")]
    miss = float(parts[0].split("=")[1])
    dly = int(parts[1].split("=")[1])
    return miss, dly


def plot_robustness_obs_sparse_delay(*, results_dir: Path, outpath: Path) -> None:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm

    df = pd.read_csv(results_dir / "robustness_results.csv")
    d = df[df["stress"] == "obs_sparse_delay"].copy()
    d["miss"] = d["severity"].map(lambda s: _parse_obs_severity(s)[0])
    d["delay"] = d["severity"].map(lambda s: _parse_obs_severity(s)[1])

    # We only report closed-loop robustness for this stress suite.
    d = d[d["method"] == "Closed-loop (ours)"].copy()
    if d.empty:
        raise ValueError("No obs_sparse_delay rows found for method='Closed-loop (ours)'.")

    miss_vals = sorted(d["miss"].unique().tolist())
    delay_vals = sorted(d["delay"].unique().tolist())

    base = d[(d["miss"] == 0.0) & (d["delay"] == 0)]
    if base.empty:
        raise ValueError("Missing base setting miss=0.0,delay=0 for obs_sparse_delay.")
    base_obj = float(base.iloc[0]["objective_mean"])

    obj_pct = np.zeros((len(miss_vals), len(delay_vals)), dtype=float)
    viol = np.zeros((len(miss_vals), len(delay_vals)), dtype=float)

    for i, mr in enumerate(miss_vals):
        for j, dl in enumerate(delay_vals):
            row = d[(d["miss"] == float(mr)) & (d["delay"] == int(dl))]
            if row.empty:
                obj_pct[i, j] = float("nan")
                viol[i, j] = float("nan")
                continue
            obj = float(row.iloc[0]["objective_mean"])
            obj_pct[i, j] = 100.0 * (obj - base_obj) / max(1e-12, base_obj)
            viol[i, j] = float(row.iloc[0]["violation_rate_mean"])

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(7.0, 2.7))
    ax1, ax2 = axes[0], axes[1]

    max_abs = float(np.nanmax(np.abs(obj_pct)))
    norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
    im1 = ax1.imshow(obj_pct, cmap="RdBu_r", norm=norm, aspect="auto")
    ax1.set_title("Objective change (%) vs nominal")
    ax1.set_xlabel("Observation delay (days)")
    ax1.set_ylabel("Missing rate")
    ax1.set_xticks(np.arange(len(delay_vals)))
    ax1.set_xticklabels([str(int(x)) for x in delay_vals])
    ax1.set_yticks(np.arange(len(miss_vals)))
    ax1.set_yticklabels([f"{x:.1f}" for x in miss_vals])
    fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

    im2 = ax2.imshow(viol, cmap="viridis", aspect="auto")
    ax2.set_title("Violation rate")
    ax2.set_xlabel("Observation delay (days)")
    ax2.set_xticks(np.arange(len(delay_vals)))
    ax2.set_xticklabels([str(int(x)) for x in delay_vals])
    ax2.set_yticks(np.arange(len(miss_vals)))
    ax2.set_yticklabels([])
    fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    fig.suptitle("Robustness: sparse/delayed observations for rolling calibration", x=0.52, y=0.98, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_runtime_breakdown(*, results_dir: Path, outpath: Path) -> None:
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    colors = _okabe_ito()

    df = pd.read_csv(results_dir / "efficiency_results.csv")
    if df.empty:
        raise ValueError("efficiency_results.csv is empty.")

    # Convert seconds to milliseconds for readability.
    methods = df["method"].tolist()
    calib_ms = (df["calib_s_mean"].astype(float) * 1000.0).to_numpy()
    disp_ms = (df["dispatch_s_mean"].astype(float) * 1000.0).to_numpy()

    x = np.arange(len(methods), dtype=float)
    fig, ax = plt.subplots(figsize=(4.4, 2.6))
    ax.bar(x, calib_ms, label="Calibration", color=colors["green"], alpha=0.9)
    ax.bar(x, disp_ms, bottom=calib_ms, label="Dispatch", color=colors["blue"], alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels([_short_method_label(m) for m in methods], rotation=25, ha="right")
    ax.set_ylabel("Runtime per cycle (ms)")
    ax.set_title("Runtime breakdown (mean per daily cycle)", loc="left")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="upper left", frameon=False)

    fig.tight_layout()
    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def plot_ablation_summary(*, results_dir: Path, outpath: Path) -> None:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    colors = _okabe_ito()

    df = pd.read_csv(results_dir / "ablation_results.csv")
    if df.empty:
        raise ValueError("ablation_results.csv is empty.")

    # Order matches the paper narrative.
    order = [
        "Full closed-loop method",
        "w/o rolling calibration (static params)",
        "w/o implementation feedback (open loop)",
        "Deterministic dispatch (no scenarios)",
        "Point forecast only (no UQ)",
    ]
    df = df.set_index("method").loc[order].reset_index()

    full_obj = float(df[df["method"] == "Full closed-loop method"]["objective_mean"].iloc[0])
    full_viol = float(df[df["method"] == "Full closed-loop method"]["violation_rate_mean"].iloc[0])

    df["obj_pct"] = 100.0 * (df["objective_mean"].astype(float) - full_obj) / max(1e-12, full_obj)
    df["viol_pp"] = 100.0 * (df["violation_rate_mean"].astype(float) - full_viol)

    labels = [
        "Full",
        "No roll.",
        "No fb.",
        "Det.",
        "Point",
    ]
    x = np.arange(len(labels), dtype=float)

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(4.4, 3.0), sharex=True)
    ax1, ax2 = axes[0], axes[1]

    ax1.bar(x, df["obj_pct"].to_numpy(), color=colors["blue"], alpha=0.9)
    ax1.axhline(0.0, color="0.2", lw=0.8)
    ax1.set_ylabel("Objective change (%)\nvs full (negative is better)")
    ax1.set_title("Ablation summary (test 2015--2020)", loc="left")
    ax1.grid(True, axis="y", alpha=0.25)

    ax2.bar(x, df["viol_pp"].to_numpy(), color=colors["orange"], alpha=0.9)
    ax2.axhline(0.0, color="0.2", lw=0.8)
    ax2.set_ylabel("Violation change (pp)\nvs full")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=0)
    ax2.grid(True, axis="y", alpha=0.25)

    fig.tight_layout()
    _ensure_parent(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render publication-quality figures for the paper.")
    parser.add_argument("--config", default="configs/default.yaml", help="YAML config path (relative to experiments/).")
    args = parser.parse_args()

    _mpl_setup()

    cfg_path = (_experiments_dir() / args.config).resolve()
    from utils.config import load_yaml

    cfg = load_yaml(cfg_path)
    paper_dir = _paper_dir()
    results_dir = (paper_dir / "results").resolve()
    fig_dir = (paper_dir / "figures").resolve()

    plot_inflow_timeseries_splits(cfg=cfg, outpath=fig_dir / "inflow_timeseries_splits.pdf")
    plot_forecast_skill_by_dam(cfg=cfg, results_dir=results_dir, outpath=fig_dir / "forecast_skill_by_dam.pdf")
    plot_forecast_calibration_tradeoff(cfg=cfg, results_dir=results_dir, outpath=fig_dir / "forecast_calibration_tradeoff.pdf")
    plot_ops_by_dam(cfg=cfg, results_dir=results_dir, outpath=fig_dir / "ops_by_dam.pdf")
    plot_runtime_value_tradeoff_v2(cfg=cfg, results_dir=results_dir, outpath=fig_dir / "runtime_value_tradeoff.pdf")
    plot_robustness_inflow_scale(results_dir=results_dir, outpath=fig_dir / "robustness_inflow_scale.pdf")
    plot_robustness_obs_sparse_delay(results_dir=results_dir, outpath=fig_dir / "robustness_obs_sparse_delay.pdf")
    plot_runtime_breakdown(results_dir=results_dir, outpath=fig_dir / "runtime_breakdown.pdf")
    plot_ablation_summary(results_dir=results_dir, outpath=fig_dir / "ablation_summary.pdf")

    print(f"Figures written under: {fig_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
