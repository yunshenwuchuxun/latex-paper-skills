from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClimatologyModel:
    doy_mean: Any  # np.ndarray shape (367,) indexed by dayofyear 1..366


def fit_climatology(*, dates, y) -> ClimatologyModel:
    """
    Fit a day-of-year mean climatology.
    """
    import numpy as np
    import pandas as pd

    d = pd.to_datetime(dates)
    y = np.asarray(y, dtype=float).reshape(-1)
    if d.shape[0] != y.shape[0]:
        raise ValueError("dates and y length mismatch")

    doy = d.dayofyear.values.astype(int)
    doy_mean = np.full((367,), np.nan, dtype=float)
    for k in range(1, 367):
        vals = y[doy == k]
        if vals.size:
            doy_mean[k] = float(np.mean(vals))

    # Fill any missing DOYs (rare) by nearest-neighbor carry.
    last = float(np.nanmean(y)) if np.isfinite(np.nanmean(y)) else 0.0
    for k in range(1, 367):
        if not np.isfinite(doy_mean[k]):
            doy_mean[k] = last
        last = doy_mean[k]
    return ClimatologyModel(doy_mean=doy_mean)


def climatology_forecast_mean(model: ClimatologyModel, *, start_date, horizon: int):
    import numpy as np
    import pandas as pd

    start = pd.Timestamp(start_date)
    out = np.zeros((int(horizon),), dtype=float)
    for h in range(int(horizon)):
        d = start + pd.Timedelta(days=h)
        k = int(d.dayofyear)
        out[h] = float(model.doy_mean[k])
    return out

