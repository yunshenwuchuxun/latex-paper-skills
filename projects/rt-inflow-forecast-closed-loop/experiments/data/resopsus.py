from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class ResOpsUSSeries:
    dam_id: int
    dam_name: str
    state: str
    df: Any  # pandas.DataFrame with a daily DatetimeIndex


def _resolve_under_experiments(*, experiments_dir: Path, relpath: str) -> Path:
    return (experiments_dir / relpath).resolve()


def load_resopsus_attributes(*, experiments_dir: Path, cfg: Dict[str, Any]):
    import pandas as pd

    p = _resolve_under_experiments(
        experiments_dir=experiments_dir,
        relpath=str(cfg["data"]["resopsus"]["reservoir_attributes_csv"]),
    )
    return pd.read_csv(p)


def load_resopsus_series(*, experiments_dir: Path, cfg: Dict[str, Any], dam_id: int) -> ResOpsUSSeries:
    """
    Load one reservoir time series and return a daily-indexed DataFrame.

    Columns are left in dataset units:
    - storage: MCM
    - inflow/outflow: m3/s
    """
    import pandas as pd

    start = str(cfg["data"]["resopsus"]["start_date"])
    end = str(cfg["data"]["resopsus"]["end_date"])
    time_series_all_dir = _resolve_under_experiments(
        experiments_dir=experiments_dir,
        relpath=str(cfg["data"]["resopsus"]["time_series_all_dir"]),
    )

    ts_path = time_series_all_dir / ("ResOpsUS_%d.csv" % int(dam_id))
    df = pd.read_csv(ts_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    df = df[(df["date"] >= start) & (df["date"] <= end)].copy()
    if df.empty:
        raise ValueError("Empty series after date filtering for dam_id=%d" % int(dam_id))

    df = df.set_index("date")
    full = pd.date_range(start, end, freq="D")
    df = df.reindex(full)

    required = ["storage", "inflow", "outflow"]
    if df[required].isna().any().any():
        # We keep this strict for reproducibility; if needed, relax and impute.
        miss = df[required].isna().mean().to_dict()
        raise ValueError("Missing required values for dam_id=%d: %s" % (int(dam_id), miss))

    attrs = load_resopsus_attributes(experiments_dir=experiments_dir, cfg=cfg)
    row = attrs[attrs["DAM_ID"] == int(dam_id)]
    if row.empty:
        dam_name = "DAM_%d" % int(dam_id)
        state = ""
    else:
        dam_name = str(row.iloc[0]["DAM_NAME"])
        state = str(row.iloc[0]["STATE"])

    return ResOpsUSSeries(dam_id=int(dam_id), dam_name=dam_name, state=state, df=df)

