from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


def _design_matrix(y, *, order: int):
    import numpy as np

    y = np.asarray(y, dtype=float)
    if order < 1:
        raise ValueError("order must be >= 1")
    if y.shape[0] <= order:
        raise ValueError("Need more samples than AR order.")
    n = y.shape[0] - order
    X = np.ones((n, 1 + order), dtype=float)
    tgt = y[order:]
    for i in range(order):
        X[:, 1 + i] = y[order - 1 - i : -1 - i]
    return X, tgt


def fit_ar_ridge(y, *, order: int, ridge: float) -> Tuple[Any, Any, float]:
    """
    Fit an AR(order) with intercept using ridge regression.
    Returns (theta, residuals, sigma).
    theta shape: (1+order,)
    """
    import numpy as np

    X, tgt = _design_matrix(y, order=order)
    # Ridge: (X^T X + ridge I)^{-1} X^T y
    XtX = X.T.dot(X)
    reg = ridge * np.eye(XtX.shape[0], dtype=float)
    theta = np.linalg.solve(XtX + reg, X.T.dot(tgt))
    pred = X.dot(theta)
    resid = tgt - pred
    sigma = float(np.std(resid, ddof=1)) if resid.shape[0] > 1 else 0.0
    return theta, resid, sigma


def ar_multistep_forecast_mean(y_hist, *, theta, order: int, horizon: int):
    import numpy as np

    y_hist = list(np.asarray(y_hist, dtype=float).tolist())
    if len(y_hist) < order:
        raise ValueError("Need at least order history points.")
    theta = np.asarray(theta, dtype=float).reshape(-1)
    out = np.zeros((horizon,), dtype=float)
    for h in range(horizon):
        # phi = [1, y_{t}, y_{t-1}, ..., y_{t-order+1}]
        phi = np.ones((1 + order,), dtype=float)
        for i in range(order):
            phi[1 + i] = y_hist[-1 - i]
        mu = float(phi.dot(theta))
        out[h] = mu
        y_hist.append(mu)
    return out


@dataclass
class RLSState:
    theta: Any  # np.ndarray shape (1+order,)
    P: Any  # np.ndarray shape (1+order,1+order)
    sigma2_ewma: float


def rls_init(*, order: int, init_ridge: float, theta0=None, sigma0: float = 1.0) -> RLSState:
    import numpy as np

    d = 1 + int(order)
    if theta0 is None:
        theta0 = np.zeros((d,), dtype=float)
    theta0 = np.asarray(theta0, dtype=float).reshape(-1)
    if theta0.shape[0] != d:
        raise ValueError("theta0 has wrong shape.")
    P0 = float(init_ridge) * np.eye(d, dtype=float)
    return RLSState(theta=theta0, P=P0, sigma2_ewma=float(sigma0) ** 2)


def rls_update(state: RLSState, *, y_t: float, phi_t, forgetting_factor: float, sigma_ewma_alpha: float) -> RLSState:
    """
    One-step RLS update with exponential forgetting.
    phi_t shape: (d,)
    """
    import numpy as np

    lam = float(forgetting_factor)
    if not (0.0 < lam <= 1.0):
        raise ValueError("forgetting_factor must be in (0, 1].")
    alpha = float(sigma_ewma_alpha)
    if not (0.0 <= alpha < 1.0):
        raise ValueError("sigma_ewma_alpha must be in [0, 1).")

    theta = np.asarray(state.theta, dtype=float).reshape(-1)
    P = np.asarray(state.P, dtype=float)
    phi = np.asarray(phi_t, dtype=float).reshape(-1)

    # Gain vector
    denom = lam + float(phi.T.dot(P).dot(phi))
    k = P.dot(phi) / denom
    # Prediction error
    err = float(y_t - phi.dot(theta))
    theta_new = theta + k * err
    P_new = (P - np.outer(k, phi.T.dot(P))) / lam

    sigma2 = alpha * float(state.sigma2_ewma) + (1.0 - alpha) * (err ** 2)
    return RLSState(theta=theta_new, P=P_new, sigma2_ewma=sigma2)


def ar_feature_from_hist(y_hist, *, order: int):
    import numpy as np

    y_hist = np.asarray(y_hist, dtype=float).reshape(-1)
    if y_hist.shape[0] < order:
        raise ValueError("Need at least order history points.")
    phi = np.ones((1 + order,), dtype=float)
    for i in range(order):
        phi[1 + i] = float(y_hist[-1 - i])
    return phi

