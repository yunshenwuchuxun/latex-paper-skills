#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt_num(x: float, digits: int) -> str:
    if x != x:  # NaN
        return "--"
    return ("{:." + str(int(digits)) + "f}").format(float(x))


def _fmt_pm(mean: float, std: float, digits: int) -> str:
    if (mean != mean) or (std != std):
        return "--"
    fmt = "{:." + str(int(digits)) + "f}"
    return fmt.format(float(mean)) + "$\\pm$" + fmt.format(float(std))


def _escape_tex(s: str) -> str:
    return s.replace("_", "\\_")


def render_forecast(results_dir: Path) -> None:
    rows = _read_csv(results_dir / "forecast_results.csv")
    by_method = {r["method"]: r for r in rows}
    methods = [
        "Persistence",
        "Climatology",
        "AR(p) static",
        "ML-LSTM",
        "Rolling AR(p) (ours)",
    ]

    lines: List[str] = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.34\\columnwidth}cccc}")
    lines.append("\\toprule")
    lines.append("Method & RMSE & NSE & CRPS & Cov. \\\\")
    lines.append("\\midrule")
    for m in methods:
        r = by_method[m]
        lines.append(
            "%s & %s & %s & %s & %s \\\\"
            % (
                m,
                _fmt_pm(float(r["rmse_mean"]), float(r["rmse_std"]), 2),
                _fmt_pm(float(r["nse_mean"]), float(r["nse_std"]), 3),
                _fmt_pm(float(r["crps_mean"]), float(r["crps_std"]), 2),
                _fmt_pm(float(r["coverage80_mean"]), float(r["coverage80_std"]), 3),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write(results_dir / "forecast_results_table.tex", lines)


def render_ops_table(
    *,
    results_dir: Path,
    csv_name: str,
    tex_name: str,
    notes_by_method: Dict[str, str],
) -> None:
    rows = _read_csv(results_dir / csv_name)
    lines: List[str] = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.34\\columnwidth}ccp{0.24\\columnwidth}}")
    lines.append("\\toprule")
    lines.append("Method & Viol. & Obj. ($\\times10^6$) & Notes \\\\")
    lines.append("\\midrule")
    for r in rows:
        note = notes_by_method.get(r["method"], "")
        lines.append(
            "%s & %s & %s & %s \\\\"
            % (
                _escape_tex(r["method"]),
                _fmt_pm(float(r["violation_rate_mean"]), float(r["violation_rate_std"]), 3),
                _fmt_pm(float(r["objective_mean"]) / 1e6, float(r["objective_std"]) / 1e6, 2),
                _escape_tex(note),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write(results_dir / tex_name, lines)


def render_robustness(results_dir: Path) -> None:
    rows = _read_csv(results_dir / "robustness_results.csv")
    rows = rows[: min(18, len(rows))]

    lines: List[str] = []
    lines.append("{\\setlength{\\tabcolsep}{2pt}\\scriptsize")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{p{0.26\\columnwidth}p{0.22\\columnwidth}p{0.30\\columnwidth}cc}")
    lines.append("\\toprule")
    lines.append("Stress & Severity & Method & Viol. & Obj. ($\\times10^6$) \\\\")
    lines.append("\\midrule")
    for r in rows:
        lines.append(
            "%s & %s & %s & %s & %s \\\\"
            % (
                _escape_tex(str(r["stress"])),
                _escape_tex(str(r["severity"])),
                _escape_tex(str(r["method"])),
                _fmt_num(float(r["violation_rate_mean"]), 3),
                _fmt_num(float(r["objective_mean"]) / 1e6, 2),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write(results_dir / "robustness_table.tex", lines)


def render_efficiency(results_dir: Path) -> None:
    rows = _read_csv(results_dir / "efficiency_results.csv")
    lines: List[str] = []
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
                _escape_tex(r["method"]),
                _fmt_num(float(r["calib_s_mean"]), 3),
                _fmt_num(float(r["dispatch_s_mean"]), 3),
                _fmt_num(float(r["total_s_mean"]), 3),
            )
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("}")
    _write(results_dir / "efficiency_table.tex", lines)


def main() -> int:
    # Run from experiments/; results live in ../paper/results.
    results_dir = (Path(__file__).resolve().parent / "../paper/results").resolve()
    render_forecast(results_dir)
    render_ops_table(
        results_dir=results_dir,
        csv_name="main_results.csv",
        tex_name="main_results_table.tex",
        notes_by_method={
            "StaticCalib-OpenLoop-DetMPC": "open-loop + static params",
            "RollingCalib-OpenLoop-DetMPC": "isolates rolling calibration",
            "RollingCalib-OpenLoop-ScenarioMPC": "isolates uncertainty-aware dispatch",
            "RollingCalib-ClosedLoop-ScenarioMPC-Feedback (ours)": "closed-loop coupling",
        },
    )
    render_ops_table(
        results_dir=results_dir,
        csv_name="ablation_results.csv",
        tex_name="ablation_results_table.tex",
        notes_by_method={
            "Full closed-loop method": "reference",
            "w/o rolling calibration (static params)": "ablate COMP-2",
            "w/o implementation feedback (open loop)": "ablate COMP-6",
            "Deterministic dispatch (no scenarios)": "ablate uncertainty propagation",
            "Point forecast only (no UQ)": "remove probabilistic forecasts",
        },
    )
    render_robustness(results_dir)
    render_efficiency(results_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
