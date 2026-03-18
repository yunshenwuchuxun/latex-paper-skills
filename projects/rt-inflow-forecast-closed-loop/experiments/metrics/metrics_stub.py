from __future__ import annotations

from typing import Any, Dict, Tuple


def _as_array(x):
    import numpy as np

    return np.asarray(x, dtype=float)


def _split_mean_sigma(predictions) -> Tuple[Any, Any]:
    """
    Accept a few lightweight representations for probabilistic predictions.

    Supported:
    - {"mu": ..., "sigma": ...} or {"mean": ..., "std": ...}
    - (mu, sigma)
    """
    if isinstance(predictions, dict):
        if "mu" in predictions and "sigma" in predictions:
            return predictions["mu"], predictions["sigma"]
        if "mean" in predictions and "std" in predictions:
            return predictions["mean"], predictions["std"]
    if isinstance(predictions, (tuple, list)) and len(predictions) == 2:
        return predictions[0], predictions[1]
    raise TypeError(
        "Probabilistic metrics require predictions as dict(mu,sigma) / dict(mean,std) or a (mu, sigma) tuple."
    )


def _rmse(pred, tgt) -> float:
    import numpy as np

    pred = _as_array(pred)
    tgt = _as_array(tgt)
    return float(np.sqrt(np.mean((pred - tgt) ** 2)))


def _mae(pred, tgt) -> float:
    import numpy as np

    pred = _as_array(pred)
    tgt = _as_array(tgt)
    return float(np.mean(np.abs(pred - tgt)))


def _nse(pred, tgt) -> float:
    import numpy as np

    pred = _as_array(pred)
    tgt = _as_array(tgt)
    denom = float(np.sum((tgt - np.mean(tgt)) ** 2))
    if denom <= 0.0:
        return float("nan")
    num = float(np.sum((pred - tgt) ** 2))
    return float(1.0 - num / denom)


def _crps_gaussian(mu, sigma, y) -> float:
    """
    Closed-form CRPS for a univariate Normal(mu, sigma) forecast.

    Formula:
      CRPS = sigma * [ z(2Φ(z)-1) + 2φ(z) - 1/sqrt(pi) ],  z = (y - mu)/sigma
    """
    import numpy as np
    from scipy.stats import norm

    mu = _as_array(mu)
    sigma = _as_array(sigma)
    y = _as_array(y)

    # Avoid divide-by-zero; sigma==0 degenerates to absolute error.
    eps = 1e-12
    sigma_safe = np.maximum(sigma, eps)
    z = (y - mu) / sigma_safe

    Phi = norm.cdf(z)
    phi = norm.pdf(z)
    crps = sigma_safe * (z * (2.0 * Phi - 1.0) + 2.0 * phi - 1.0 / np.sqrt(np.pi))
    # For sigma ~ 0, CRPS -> |y-mu|.
    crps = np.where(sigma <= eps, np.abs(y - mu), crps)
    return float(np.mean(crps))


def _coverage80_gaussian(mu, sigma, y) -> float:
    """
    Empirical 80% central interval coverage under a Normal(mu, sigma) forecast.
    """
    import numpy as np
    from scipy.stats import norm

    mu = _as_array(mu)
    sigma = _as_array(sigma)
    y = _as_array(y)

    # Central 80% interval => alpha=0.1, 0.9.
    z = float(norm.ppf(0.9))
    lo = mu - z * sigma
    hi = mu + z * sigma
    covered = (y >= lo) & (y <= hi)
    return float(np.mean(covered.astype(float)))


def compute_metrics(*, predictions, targets, metrics: list[str]) -> dict[str, float]:
    """
    Compute standard forecast metrics.

    Notes:
    - For point metrics (rmse/mae/nse), pass predictions and targets as array-like.
    - For probabilistic metrics (crps/coverage80), pass predictions as either:
      * {"mu": array_like, "sigma": array_like}, or
      * (mu, sigma)
    """
    out: Dict[str, float] = {}
    mset = [m.strip().lower() for m in metrics]
    for m in mset:
        if m == "rmse":
            out[m] = _rmse(predictions, targets)
        elif m == "mae":
            out[m] = _mae(predictions, targets)
        elif m == "nse":
            out[m] = _nse(predictions, targets)
        elif m == "crps":
            mu, sigma = _split_mean_sigma(predictions)
            out[m] = _crps_gaussian(mu, sigma, targets)
        elif m in ("coverage80", "cov80", "coverage"):
            mu, sigma = _split_mean_sigma(predictions)
            out["coverage80"] = _coverage80_gaussian(mu, sigma, targets)
        else:
            raise ValueError(f"Unknown metric: {m}")
    return out

